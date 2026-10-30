# Board · Shelf · Canvas 아키텍처

2026-10-26 설계. 관련 이슈: [#3 개발 기반](https://github.com/Blueprint4Agent/Canvanity/issues/3), [#4 편집 엔진](https://github.com/Blueprint4Agent/Canvanity/issues/4), [#5 도메인 설계](https://github.com/Blueprint4Agent/Canvanity/issues/5).

| 문서                                     | 내용                                            |
| ---------------------------------------- | ----------------------------------------------- |
| [도메인과 데이터](domain-model.md)       | ERD·필드·제약·트랜잭션·게시 상태·마이그레이션   |
| [멤버십과 권한](membership-policy.md)    | 역할·등급·상태·Shelf 정책·허용/거부 행렬        |
| [API 명세](api-design.md)                | 요청/응답·권한·동시성·목록·오류·화면 경로       |
| [등급 설정 API](grade-management.md)     | 이름·순서·기본값·삭제 대체·감사·예외 기본 메시지 |
| [기존 계정 수동 초대](member-invitations.md) | invite Board의 등록·기본 등급·제재 보호·감사 |
| [Board 기본 설정](board-settings.md) | 소개·규칙·관심사·공개/가입 정책·보관/복원 |
| [소유권·종료](board-lifecycle.md) | Owner 위임·보관 Board 삭제·계정/파일 경계 |
| [Shelf 관리·정책](shelf-management.md) | 분류 CRUD/정렬·직접 조회·기본/재정의 등급 정책·현재 구현 경계 |
| [Canvas 초안 기반](canvas-drafts.md) | 작성자 전용 메타데이터·JSONB 초기 문서·Shelf 이동·휴지통/복구·삭제 경계 |
| [개발과 검증](development-validation.md) | 현행 환경 감사·독립 fixture·실행·정리·검증 결과 |
| [편집 엔진 검토](editor-decision.md)     | 후보·선정 근거·문서 어댑터·브라우저 실험과 한계 |

## 결정과 적용 범위

Board는 커뮤니티, Shelf는 Board 내부의 운영 분류, Canvas는 게시글 메타데이터와 편집 문서다. MVP 게시글에는 Board와 기본 Manual Shelf가 반드시 있다. Profile 대표 홈과 My Canvas는 독립 게시글이 아니다. Plaza는 여러 Board/공개 게시글을 발견하는 조회 표면이다.

Board 홈의 UI Canvas는 `widgets`, 게시글 Content Canvas는 `nodes/edges`로 저장한다. 카메라·미니맵·렌더링 기술을 공유할 수 있으나 저장 문서·권한·API는 분리한다. UI Canvas의 공식 배치는 운영자가 편집하며 일반 방문자의 팬/줌은 임시 상태다.

회원에게는 운영 역할과 활동 등급을 별도로 부여한다. 뉴커머 등급이라고 운영 역할이 생기지 않고, Moderator라고 타인의 비공개 초안을 읽지 않는다. 회원 등급·수동 승급·등급별 읽기/글쓰기/댓글 정책은 기본 구현 범위다.

이 디렉터리의 전체 명세는 **단계별 구현의 기준**이다. 개설·조회·빈 보드 삭제 API와 화면은 [사용자 Board 개설 흐름](board-creation.md), 회원 운영과 등급 설정 API는 각 구현 계약을 따른다. 구현·검증·main 병합·배포는 이슈/PR 상태로 구분한다. 미구현 콘텐츠 경로를 배포 OpenAPI에 선행 노출하지 않는다. 실제 구현과 같은 변경에서 양쪽 OpenAPI와 생성 타입을 갱신한다. 검증용 DDL/편집기는 제품 마이그레이션·편집기로 사용하지 않는다.

## 구현 순서와 완료 경계

1. 이 문서의 도메인/정책/API 설계와 검증 기반을 확정한다. 엔진의 미검증 입력은 별도 채택 조건으로 남긴다.
2. #22/#23: Board·기본 등급/정책·Owner·Shelf·기본 홈을 한 트랜잭션으로 생성한다. 서버 권한 평가기를 먼저 적용한다.
3. #8의 최소 메타데이터/빈 문서 생성과 #24 자유 Tag를 연결한다.
4. #6/#7: 에셋·문서 저장·충돌/복구를 연결한다.
5. #8의 게시/게시 취소/공개 조회/Plaza까지 실제 수직 흐름을 검증한다.
6. #25/#26: 공식 홈 편집·댓글/좋아요/구독/통계를 구현한다.

Smart Shelf·활동량 자동 승급·가입 승인/초대·다중 Shelf·독립 개인 문서·여러 Board 공유·개인 배치·공동 편집·큰 공용 공간은 후속이다. 자동 승급을 도입해도 아래 등급/권한 모델은 유지한다.

기본 등급은 **Newcomer(뉴커머) → Pinner(피너) → Curator(큐레이터)**이며 rank는 0/10/20이다. Board 운영자는 이름·순서와 Shelf 이용 정책을 변경할 수 있고, 등급 이름을 바꿔도 grade_id 참조는 유지한다.


## 구현 진행 추적

현재 진행은 [전체 로드맵 #1](https://github.com/Blueprint4Agent/Canvanity/issues/1), [Board·회원 운영 #22](https://github.com/Blueprint4Agent/Canvanity/issues/22), [Shelf #23](https://github.com/Blueprint4Agent/Canvanity/issues/23)에서 확인한다. [공개 가입·탈퇴 API #29](https://github.com/Blueprint4Agent/Canvanity/issues/29)는 PR #30으로 main에 반영했다. 로컬 구현·검증·게시·main 병합을 구분해 체크한다. 사용자 요청으로 신규 UI는 보류하고 백엔드 API·권한·계약부터 진행한다.


회원 운영 #31/PR #33과 등급 설정 #32/PR #34는 main에 반영했다. 초대 #35/초안 PR #36, 기본 설정 #37/초안 PR #38, [#39 소유권·종료](https://github.com/Blueprint4Agent/Canvanity/issues/39)/초안 PR #40, #23 Shelf 관리/초안 PR #41은 main 미병합이다. 현재 #8의 Canvas 초안·메타데이터·빈 문서와 Shelf 소속/삭제 경계를 feat/shelf-management 기준으로 분리해 진행한다. UI는 제외하며 각 이슈에서 구현·검증·게시·main 병합을 구분한다. 문서 저장은 #7, Tag는 #24, 공개 목록/게시와 실제 에셋/삭제 outbox는 #8/#6에서 이어간다.
