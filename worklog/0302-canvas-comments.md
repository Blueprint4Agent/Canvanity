# Commit Title

feat: 캔버스 댓글과 운영 숨김을 구현한다

# Changed File Scope

Canvas 댓글 모델/저장소·서비스·라우터·0032 migration, API/SQLite/PostgreSQL 검사·양쪽 계약/생성 타입과 한국어 문서.

# Reason

2026-11-10 사용자 요청의 독립 단위 #64를 좋아요 PR #67/head69b823f 다음으로 구현한다. 구현 전에 feat/canvas-comments와 이 계획을 만든다. 선행 PR과 분리해서 검토한다.

# Design

게시본의 현재 읽기 정책을 공유하고 활성 회원의 create_comment 정책으로 1..5000자 댓글을 작성한다. 최신순 created_at/id keyset cursor와 visible 기본 목록, Board 운영진만 사용하는 all 목록을 제공한다. 본인 visible 댓글만 수정하고 본인 또는 현재 Board 운영진은 삭제할 수 있다. Owner/Admin/Moderator는 이유와 함께 숨김/복원한다. 독립 revision CAS/no-op·삭제 tombstone으로 충돌/감사 경계를 유지한다. 삭제 본문은 비우며 숨김 본문은 목록/단건에서 작성자·운영진만 접근한다. 공개 응답은 서버 capabilities와 허용 필드만 제공한다. 같은 Board 쓰기 잠금과 현재 User/Canvas 잠금을 재사용한다. 계정 삭제는 author/moderator SET NULL, Canvas/Board 영구삭제는 CASCADE다.

# Verification Plan

API/세션·본문/커서 형식·SQLite 페이지/권한/수명주기/CAS/rollback, 실제 격리 PostgreSQL migration/동시 수정·보존을 확인한다. VERIFY_BASE=69b823f로 루트 verify-plan→verify와 정상 훅/ready PR·실제 거버넌스를 수행한다.

# Impact

새 댓글 테이블/API를 추가하며 Canvas metadata/document/publication clock은 유지한다. 답글·알림·새 제품 UI·운영 배포는 별도다. 좋아요 PR #67 이후 의존 PR로 게시한다.

# Loop Alignment

요청 → optional/세션 인증 → 댓글 서비스 → 공용 현재 정책 → 저장소 트랜잭션 → capabilities/응답. 실시간/작업 큐/데스크톱은 후속 소비자가 없어 해당 없음.

# Verification

- API/SQLite16개7.55초 통과: 본문/필드/세션 검증, 작성자·운영진 경계, CAS/no-op·운영 숨김/복원·삭제 tombstone, 페이지/사용자 cursor·현재 제재/게시 취소·commit rollback·작성자 삭제 뒤 숨김 비노출을 확인했다.
- 실제 localhost PostgreSQL 고유 schema에서 댓글/좋아요2개4.25초, 기존 Tag/layout/publication 회귀3개8.98초 통과했다. 동시 댓글 수정 단일 승자·409와 migration 자료 보존/빈 왕복·자료 있는 downgrade 거부·author SET NULL·Canvas CASCADE·고유 schema 제거를 확인했다.
- 책임 경계 수동 검토: 새 라우터는 전송/서비스 호출만 담당하고 서비스는 공용 Access/Permission의 공개 메서드를 사용한다. 댓글 SQL/ORM 쓰기·트랜잭션/오류 변환은 모델 저장소가 소유하며 다른 서비스의 비공개 메서드 호출은 없다. 저장소 transaction_type 확장은 기존 트랜잭션 수명주기를 그대로 재사용한다.
- 기준69b823f의 루트 verify-plan은 모델/계약/미등록 영향으로 전체15명령을 선택했고 make verify가780.8초에 통과했다. frontend221/UI259/production18/style3·타입/계약·브랜딩/패키징을 확인했다. 신규 UI·실시간·데스크톱·운영 배포는 범위 밖이며 분류기가 선택한 전체 프런트 검사를 유지했다.

# State Ownership

댓글 상태·revision은 DB, 현재 액션은 서비스/공유 정책이 소유한다. 프런트는 계약/생성 타입만 갱신한다.

# Memoization

프런트 런타임 변경 없음.

# Performance Evidence

본문 JSONB 대신 댓글만 조회하고 limit+1 keyset으로 범위를 제한한다. 실제 SQL/경쟁 결과는 검증 후 기록한다.

# Page Family

## Family

해당 없음: 백엔드 API/계약.

## Reference

Canvas 공개본/좋아요와 Board 권한.

## Shared Rules

공용 Access/Permission과 저장소 소유 트랜잭션을 재사용한다.

## Exceptions

없음.

## Evidence

신규 화면 변경은 없다. 실제 API/SQLite16개와 격리 PostgreSQL 댓글/좋아요2개·기존 회귀3개로 기능·경쟁·보존을 확인했다. 전체 검증/게시 결과는 위 Verification에 기록한다.
