# 사용자 Board 개설 흐름

[아키텍처](README.md) · [회원 등급·권한](membership-policy.md)

## 이번에 구현한 범위

사용자 요청에 따라 회원/등급 관리보다 **첫 Board 만들기**를 우선했다.

1. `/board`에서 실제 보드를 둘러보거나 내가 만든 보드·이름으로 검색한다. 비회원은 로그인 후 `/board`로 돌아온다.
2. 공용 모달에서 이름·주소(slug)·소개·공식 관심사 최대 3개·공개 범위를 정한다.
3. 공개는 public/open, 비공개는 private/invite로 생성한다. 비공개 보드는 개설자만 접근하는 상태로 시작하며 초대 관리 UI는 후속이다.
4. 생성 완료 후 `/b/{slug}` 기본 홈으로 이동한다. 소개·관심사·Owner/등급·기본 Shelf와 게시글 빈 상태를 표시한다.
5. 개설자가 잘못 만든 빈 보드는 주소를 직접 입력해 삭제할 수 있다. 다른 회원/게시글 등 제한 참조가 있으면 삭제하지 않는다.

기존 예시 주제 카드·Plaza 주제 바로가기 대신 실제 API 목록을 사용한다. 글 작성·가입/초대·등급/운영진/Shelf 편집·공식 홈 자유 배치는 이번 개설 흐름에 포함하지 않는다. 기본 정책은 저장·평가하지만 해당 관리 API/UI는 후속이다.

## 서버 원자성과 기본 데이터

migration `0024_board_creation`은 Board, 공식 Interest 연결, 회원 등급·멤버, Board/Shelf 액션 정책, 기본 Shelf, 홈 문서, 생성 감사 테이블을 추가한다. 기존 사용자/프로필/공식 Interest는 보존한다.

생성 서비스가 같은 DB 세션에서 다음을 저장한 뒤 한 번만 commit한다.

- Board와 Owner 활성 멤버(개설자, 기본 뉴커머 등급).
- 뉴커머(Newcomer) rank 0, 피너(Pinner) 10, 큐레이터(Curator) 20. 기본 등급은 뉴커머다.
- 공지사항 Shelf와 기본 자유 이야기 Shelf.
- 액션별 Board 기본 정책과 공지의 운영 역할 전용 작성/댓글 정책.
- 기본 소개·Shelf·최신 글 위젯을 가진 공식 홈 JSONB와 생성 감사 기록.

사용자 행 잠금과 수량 재검사로 동시 생성 시에도 개설 한도 20개를 보장한다. slug 고유 제약이 경쟁 요청을 최종 판정하며 중간 실패는 전부 rollback한다. 이름에 따라 회원 권한을 판단하지 않고 grade_id/rank와 role/status/policy를 따로 평가한다. Curator Member는 공지를 작성할 수 없다.

## 제공 API

Board API는 Bearer 세션을 사용한다. 공개 GET은 무인증도 가능하며, 인증된 요청은 현재 멤버 상태로 다시 필터링한다. API key 인증 지원은 이번 Board 범위에 추가하지 않는다. 응답은 `private, no-store`다.

| Method | Endpoint                      | 동작                                                                   |
| ------ | ----------------------------- | ---------------------------------------------------------------------- |
| GET    | /api/v1/boards                | q/interest_id/mine/limit/cursor, 공개 또는 접근 가능한 Board 목록      |
| POST   | /api/v1/boards                | 로그인 사용자 개설, 201·Location·BoardSummary                          |
| GET    | /api/v1/boards/by-slug/{slug} | BoardHomeResponse                                                      |
| GET    | /api/v1/boards/{id}           | 같은 Board aggregate 홈 응답                                           |
| GET    | /api/v1/boards/{id}/home      | 소개·현재 멤버십·등급·허용 Shelf/액션·기본 레이아웃                    |
| DELETE | /api/v1/boards/{id}           | Owner·현재 revision·정확한 confirm_slug, 다른 회원 없는 빈 Board만 204 |

목록의 cursor는 검색 필터와 마지막 created_at/id를 포함한다. 정렬과 권한을 서버에서 다시 적용하고 잘못된 cursor는 422로 거부한다. 비공개·정지·차단된 객체는 404로 숨긴다. 첫 단계에서 GET /boards/{id}는 단독 메타데이터 대신 홈 aggregate를 반환하는 것으로 계약을 구체화했다.

기존 광범위 설계의 보관 후 영구 삭제는 후속이다. 이번 DELETE는 **새로 만든 빈 Board의 되돌리기**만 허용한다. 다른 멤버/후속 콘텐츠 FK가 있으면 409다. 향후 파일·게시글·소유권 이전을 도입할 때 종료/정리 outbox를 함께 확장한다. 계정 삭제는 소유 Board가 있으면 명시적인 BOARD_OWNERSHIP_REQUIRED(409)를 반환하며 먼저 빈 Board를 삭제할 수 있다.

## 클라이언트 상태와 화면

`BoardPage → useBoards/useBoardActions → boardsApi → 생성 타입 → 서버` 경로를 따른다. BoardHomePage도 같은 도메인 훅으로 읽는다. 조회 key에 계정/검색/보드 주소를 포함하고, 계정 전환/경로 변경 시 이전 요청을 취소해 다른 계정의 결과를 숨긴다. 폼은 초안만 소유하며 실패 시 입력을 유지한다. 중복 submit은 진행 중 요청으로 잠근다.

공용 Modal/InputField/TextareaField/SegmentedControl과 기존 ProfileInterestsField를 재사용한다. 관심사 선택기는 maxSelections 기본 8을 유지하고 Board만 3으로 제한한다. 제품에 새 상태 라이브러리나 편집 엔진을 추가하지 않았다. 한국어 기본·기존 영어 전환·CommunityCanvas 카메라/미니맵을 유지한다. `/b/{slug}`에서도 Board 메뉴의 aria-current와 브랜드의 복귀 경로를 유지한다.

## 검증

- SQLite API/통합: 생성·초기화·공개/비공개·중복·잘못된 관심사·생성 실패 롤백·cursor·현재 제재·확인 삭제·계정 삭제 보호.
- PostgreSQL opt-in 통합: 실제 전체 Alembic 업그레이드, UUID/JSONB/등급 복합 FK, 동일 slug 경쟁·19개 상태의 한도 경쟁·삭제·다운그레이드/재업그레이드. 고유 schema를 삭제하고 부재를 확인한다.
- 브라우저 mock: 390/1440 × light/dark, 관심사 3개 한도·중복 주소 후 입력 유지·생성/홈/새로고침·비회원/비공개 거부.
- 실제 브라우저: 격리 FastAPI/SQLite·메모리 Redis·로컬 파일, 실제 로그인→개설 POST 201→홈 GET→reload·공개 무인증 읽기·비공개 목록/상세 차단. 이메일/OAuth/Stripe와 외부 worker는 사용하지 않는다.

PostgreSQL 검사는 기본 suite에서 skip하며 다음처럼 명시 실행한다. 현재 backend 설정이 localhost PostgreSQL인지 검사하고 기존 테이블을 수정하지 않는다.

```bash
cd src/backend
CANVANITY_TEST_POSTGRES=1 TRACING_ENABLED=false uv run pytest tests/integration/api/v1/board/test_board_postgres.py
```

마이그레이션 연결 주입은 [Alembic 공식 connection sharing 방식](https://alembic.sqlalchemy.org/en/latest/cookbook.html#sharing-a-connection-across-one-or-more-programmatic-migration-commands)을 따른다. 보통 런타임은 기존 엔진 생성 흐름을 유지하며 테스트만 고유 schema 연결을 주입한다.

검증 결과와 로컬 화면 증거는 worklog/0275-board-membership-shelves.md를 따른다.


## Board 데이터 접근 계층

DB 쿼리·세션·행 잠금·flush/commit과 롤백 경계는 기존 `app/models/board.py` 안의 `BoardRepository`와 `BoardTransaction`이 담당한다. 별도 Repository 파일을 만들지 않는다. `BoardService`는 Repository와 `BoardPermissionService`를 FastAPI 생성자 DI로 주입받아 현재 권한·상태·한도 판단과 응답 구성을 수행한다. 변경 권한은 모델 트랜잭션의 잠금을 유지하는 동안 검사한다. Board 서비스의 직접 DB import는 아키텍처 검사에서 거부한다.


## 공개 Board 가입·탈퇴 API


개설 이후의 첫 참여 흐름으로 `POST /api/v1/boards/{board_id}/join`과 `DELETE /api/v1/boards/{board_id}/membership`을 추가한다. 두 API는 Bearer 세션만 허용한다. 이번 단계는 API/계약만 제공하며 가입·탈퇴 UI는 보류한다.

- public/open의 active Board 가입은 현재 `is_default` 등급과 `member/active` 상태를 부여한다. 요청자가 역할이나 등급을 지정할 수 없다. 이미 active 회원이면 변경·감사 중복 없이 현재 멤버십을 반환한다.
- private/invite의 새 가입은 거부하며 기존 사용자 초대는 다음 관리 작업이다. archived Board는 새 가입을 거부하고 suspended Board는 조회·가입·탈퇴를 거부한다.
- Owner 탈퇴는 `409 BOARD_OWNER_CANNOT_LEAVE`다. 소유권 이전이나 보드 정리 경로를 사용해야 한다. 일반 active 회원은 탈퇴할 수 있으며 재가입 시 현재 기본 등급을 받는다. suspended/banned/pending 상태를 탈퇴·재가입으로 지울 수 없다.
- 가입/탈퇴는 Board 행 잠금 아래 현재 상태를 확인하고 멤버십·revision·감사 기록을 하나의 트랜잭션으로 저장한다. 탈퇴는 기존 콘텐츠의 자동 삭제를 의미하지 않으며 게시글 구현 시 작성자 참조 정책을 별도로 연결한다.

`BoardPermissionService`가 현재 Board/멤버 상태·역할·등급·정책을 평가한다. FastAPI가 이 평가기를 `BoardService`와 `BoardMembershipService`의 생성자에 주입한다. 라우터는 서비스를 주입받고, 서비스에는 `models/board.py`의 `BoardRepository`를 주입한다. 쿼리·세션·행 잠금·추가/삭제·commit/롤백은 같은 모델 파일의 Repository와 BoardTransaction이 담당한다. 서비스는 DB 세션을 직접 사용하지 않으며 잠금 문맥 안에서 현재 권한과 한도를 판단한다. 등급은 운영 역할이 아니며 앱 전역 관리자는 Board 운영진으로 자동 승격하지 않는다. 후속 Shelf/Canvas 서비스는 같은 평가기를 주입받아 사용한다.

후속 운영 순서는 회원 목록·등급/역할·제재 관리와 기존 계정 초대, Board 정보 수정, 소유권 위임·보관/종료다. 이메일/링크 초대·자동 승급·임의 운영 역할 편집은 이 구현에 포함하지 않는다.
