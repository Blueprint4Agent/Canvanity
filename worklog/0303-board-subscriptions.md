# Commit Title

feat: 보드 구독과 본인 구독 피드를 구현한다

# Changed File Scope

Board 구독 관계/저장소·서비스·라우터·0033 migration, 기존 공개 Feed의 구독 필터, API/SQLite/PostgreSQL 검사·양쪽 계약/생성 타입과 한국어 문서.

# Reason

2026-11-10 사용자 요청의 독립 단위 #65를 댓글 PR #68/headf64240f 다음으로 구현한다. 구현 전에 feat/board-subscriptions와 이 계획을 만든다. 가입(권한)과 구독(피드 선택)을 구분한다.

# Design

세션 전용 GET/PUT/DELETE /boards/{id}/subscription과 GET /me/subscriptions/canvases를 제공한다. 공개 Board는 비회원도 구독할 수 있고 private은 현재 활성 회원만 허용한다. 등록은 active Board만, 취소는 읽을 수 있는 archived Board에서도 허용한다. 현재 User/Board 잠금·정책을 적용하고 복합 PK와 두 FK CASCADE로 중복/삭제를 보호한다. 가입/탈퇴·Board revision은 변경하지 않는다. 공개 Feed의 단일 statement에 본인 구독 관계를 추가해 현재 Board/Shelf/공개본 권한과 Interest/Tag·최신순 cursor를 재사용한다. cursor scope는 사용자에 결합하고 매 페이지 현재 구독·권한을 다시 적용한다.

# Verification Plan

API/세션·query 계약, SQLite 멱등성·가입 독립성·현재 제재/비공개·구독 피드/커서·rollback과 실제 격리 PostgreSQL migration/동시 등록·FK/현재 피드를 검사한다. VERIFY_BASE=f64240ffb34e8905db5af0a20a35b2b9e275b13d make verify-plan→make verify, 정상 훅/ready PR·실제 거버넌스를 수행한다.

# Impact

구독 테이블과 API를 추가한다. 기존 공개 Feed 기본값/응답과 가입 권한은 유지한다. 새 UI·알림·추천·운영 DB migration/배포는 별도다. 댓글 PR #68 이후 의존 PR로 게시한다.

# Loop Alignment

요청 → 세션 → 구독 서비스/기존 Feed → 현재 정책/모델 트랜잭션·단일 snapshot → 응답. 실시간·작업 큐·데스크톱은 후속 소비자가 없어 해당 없음.

# Verification

- API/기존 Feed/SQLite의73개가6.45초에 성공했다. 남은 SQLite 시나리오는 Board revision의 실제 home 응답 경로와 private/invite 정책 쌍을 보완한 뒤1개2.75초에 통과했다. 구독/가입 독립성·동일 행/시각 보존·private 전환·보관/취소·현재 제재/게시 취소·commit rollback을 확인했다.
- 실제 localhost PostgreSQL 고유 schema의 구독1개1.97초, 기존 Tag/layout/publication/feed 회귀4개9.67초 통과했다. 동시 등록5개 단일 행·migration 자료 보존/빈 왕복·자료 있는 downgrade 거부·사용자 cursor·페이지 간 제재·계정 CASCADE와 schema 제거를 확인했다.
- 첫 루트 실행은 기준 SHA 마지막 글자 오타로 테스트 시작 전에 종료됐다. 실제 HEAD f64240ffb34e8905db5af0a20a35b2b9e275b13d를 확인해 수정했고 올바른 기준의 전체 검증을 진행한다. 범위를 수동 축소하지 않았다.
- 책임 경계 검토: 구독 서비스는 현재 Board/계정 판단을 조합하고 SQL/ORM 쓰기·commit/오류 변환은 Board 저장소가 소유한다. Feed의 private SQL builder는 같은 저장소 내부에서만 재사용하고 서비스는 공개 read 인터페이스를 사용한다. 새 전송 우회·비공개 서비스 호출은 없다.
- 올바른 기준 f64240f의 verify-plan은 모델/계약/미등록 영향으로 전체15명령을 선택했고 make verify가703.2초에 통과했다. frontend221/UI259/production18/style3·양쪽 계약/생성 타입·브랜딩/모놀리식 패키징을 확인했다. 신규 UI·작업 큐·데스크톱·운영 배포는 해당 없으며 전체 프런트 회귀를 유지했다.

# State Ownership

구독 관계는 DB, 접근 권한은 현재 Board/Shelf 정책, Feed header는 공개 snapshot이 소유한다. 프런트는 계약/생성 타입만 갱신한다.

# Memoization

프런트 런타임 변경 없음.

# Performance Evidence

구독 필터를 기존 Feed의 SQL에 적용하고 본문/N+1 조회를 추가하지 않는다. 실제 SQL/경쟁은 검증 후 기록한다.

# Page Family

## Family

해당 없음: 백엔드 API/계약.

## Reference

Board 가입/탈퇴와 공개 Feed.

## Shared Rules

공용 Board 정책과 저장소 소유 SQL/트랜잭션을 재사용한다.

## Exceptions

없음.

## Evidence

API/기존 Feed·SQLite74개와 실제 PostgreSQL 구독1개·관련 회귀4개로 기능·현재 권한·경쟁·보존을 확인했다. 신규 화면 변경은 없으며 전체 검증/게시 결과는 위 Verification에 기록한다.
