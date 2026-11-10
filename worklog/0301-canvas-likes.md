# Commit Title

feat: 캔버스 좋아요와 현재 권한 조회를 구현한다

# Changed File Scope

Canvas 좋아요 모델/저장소·서비스·라우터·0031 migration, API/SQLite/PostgreSQL 검사, 양쪽 OpenAPI·생성 타입과 한국어 문서.

# Reason

2026-11-10 사용자 요청에 따라 기존 PR #61과 #62를 순서대로 확인·병합했다. main eb9f3f3에서 #26의 좋아요를 첫 독립 완료 단위로 시작한다. 댓글·구독·통계와 신규 제품 UI는 별도 작업이다.

# Design

GET/PUT/DELETE /canvases/{id}/like는 게시본만 대상으로 현재 Board/회원/Shelf 읽기 권한을 적용한다. PUT/DELETE는 활성 세션·현재 react 액션을 요구한다. CanvasAccessService의 명시적 publication 읽기와 Board→User→Canvas 잠금 순서를 재사용하고, 변경은 Board 배타 잠금으로 현재 정책 변경·게시/취소와 직렬화한다. (canvas_id,user_id) 기본키와 FK CASCADE로 중복/삭제를 보호한다. 응답은 현재 count와 본인 liked만 공개하고 회원 명단은 제공하지 않는다. 재게시/게시 취소/휴지통은 행을 보존하며 비공개 상태에서는 집계를 숨긴다. Canvas/계정 영구삭제는 FK로 정리한다. metadata/document/publication clock은 변경하지 않는다.

# Verification Plan

API 인증/계약·SQLite 멱등성/등급/제재/게시 상태/실패 롤백·실제 격리 PostgreSQL migration/경쟁 요청/권한 변경을 검사한다. 계약 동기화 후 VERIFY_BASE=eb9f3f3dc0679e4f745ecb77402e4d37c0e20e2e make verify-plan → make verify, 정상 commit-msg/pre-push와 ready PR 메타데이터/거버넌스를 확인한다.

# Impact

새 좋아요 테이블/API를 추가한다. 기존 본문/공개 snapshot은 유지하며 UI·알림·운영 배포는 해당하지 않는다. 기존 PR 병합 트리가 각 검증 head와 같고 리뷰/대화/필수 상태 차단이 없음을 확인했다. 과거 worklog는 수정하지 않는다.

# Loop Alignment

요청 → 세션/optional 인증 → 좋아요 서비스 → 공용 현재 권한 → 저장소 트랜잭션 → 응답. 실시간/작업 큐는 후속 소비자가 없어 추가하지 않는다. 프런트는 계약/생성 타입만 갱신하며 UI·데스크톱 복구는 해당 없음.

# Verification

- API/SQLite/현재 인증 정책48개가25.54초에 통과했다. 초기 테스트에서 optional OpenAPI security 합성과 정책 응답 actions 필드를 기존 계약에 맞췄다.
- 실제 localhost PostgreSQL 고유 schema에서 좋아요 검증1개1.53초 통과: 0030 자료 보존·0031 upgrade/빈 downgrade 왕복·자료 있는 downgrade 거부·동시 PUT6개/DELETE4개·실제 유니크 위반·Board row 잠금 대기 뒤 보관 상태 재검사·계정 삭제 CASCADE·schema 제거를 확인했다. 초기 fixture의 home 호출을 실제 keyword 계약에 맞췄다.
- 새 head를 기대하는 기존 startup/Tag/publication/layout migration 검사를 갱신했고, Board 미디어 전용 migration 검사는0030에 고정해 해당 downgrade 불변식을 유지했다. 영향받은 실제 PostgreSQL 회귀4개12.18초 통과했다.
- 루트 VERIFY_BASE=eb9f3f3의 verify-plan은 모델/계약/미등록 영향으로 전체15명령을 선택했고 make verify가462.4초에 통과했다. 프런트 단위221/브라우저259/production18/style3, 기존 제공자 계약·타입·브랜딩·모놀리식 패키징을 확인했다. 새 UI가 없어 별도 화면 작업은 해당 없으며 전체 프런트 회귀는 분류기의 선택대로 유지했다. 운영 DB migration/배포는 수행하지 않는다.
- 책임 경계 수동 검토: 라우터는 서비스에 위임하고 서비스는 SQL/세션/드라이버 오류를 직접 다루지 않는다. 공용 Access/Permission의 공개 메서드를 사용하며 저장소가 flush/commit·오류 변환을 소유한다. 새 전송 우회나 비공개 서비스 호출은 없다.

# State Ownership

좋아요 관계/집계는 DB, 현재 권한은 공용 Board 정책이 소유한다. 프런트 런타임 변경 없음.

# Memoization

프런트 런타임 변경 없음.

# Performance Evidence

본문 JSONB를 읽지 않고 좋아요 관계만 집계한다. 실제 SQL/경쟁 결과는 검증 후 기록한다.

# Page Family

## Family

해당 없음: 백엔드 API/계약.

## Reference

기존 Canvas publication/API와 공용 권한.

## Shared Rules

저장소가 SQL/트랜잭션을 소유하고 서비스가 권한/업무 흐름을 담당한다.

## Exceptions

없음.

## Evidence

신규 UI가 없어 기존 화면 비교는 해당 없음. 실제 API/SQLite48개와 격리 PostgreSQL1개/기존 회귀4개로 권한·경쟁·보존을 확인했다. 전체 프런트 검사와 게시 결과는 위 Verification에 기록한다.
