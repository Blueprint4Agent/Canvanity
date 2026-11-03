# Commit Title

feat: 캔버스 게시 스냅샷과 공개본 열람을 구현한다

# Changed File Scope

- Canvas 게시/게시 취소·공개본 metadata/document와 이미지 읽기, 기존 모델/가드·서비스/라우터·오류와 migration.
- API/SQLite/실제 격리 PostgreSQL·공통 인증 회귀, 한국어 설계/구현 문서와 양쪽 OpenAPI·생성 타입.
- 구현 중 사용자 오류로 추가한 startup의 Alembic 단독 스키마 소유·명시적 init_db helper 경계·재현/회귀 및 시작 안내.

# Reason

선행 #47/PR #48의 본문 CAS와 #49/PR #50의 자유 Tag가 main 9cc741d에 반영됐다. 명시적 게시 snapshot을 다른 사용자에게 제공하고 이후 초안 변경과 공개본을 분리한다. 상위 #8의 UI/목록과 분리한 백엔드 완료 단위 #51을 추적한다.

# Design

- 구현 중 확인한 추가 범위: 자동 reload가 새 모델을 읽은 뒤 `0029` 파일이 생기기 전에 startup의 Alembic→`init_db/create_all`이 실행되어 실제 DB가 revision0028/새3테이블 존재 상태가 됐다. 사용자 오류와 부모 세션의 read-only schema·빈 행 검증으로 원인을 확인했다. 부모가 실제 DB를 데이터 보존 방식으로 복구하며, 이 브랜치는 startup의 create_all 호출만 제거해 Alembic이 스키마를 단독 소유하도록 고친다. 명시적 init_db API는 유지하고 pending 모델/이전 migration head를 가진 격리 SQLite로 재현·회귀를 검증한다. blind IF NOT EXISTS·migration 우회/테스트 완화는 추가하지 않는다.
- 구현 전 확정: `Canvas.status=draft/trashed`는 편집/휴지통 수명주기로 유지한다. 게시 상태는 별도 counter/snapshot/tag 테이블의 축이다. 기존 Canvas 부모를 재생성하거나 CHECK/FK를 바꾸지 않고 0028 다음 migration에서 새 테이블만 추가해 SQLite/PG 기존 자식을 보존한다.
- 지속 `publication_revision`은 현재 공개 상태의 CAS token이다. 최초 0이며 실제 publish/교체·unpublish·휴지통의 공개본 제거마다 1 증가한다. 게시 취소 뒤에도 counter는 남아 ABA와 번호 재사용을 막는다. 같은 상태/source의 no-op은 번호를 유지하되 모든 기대 revision 검사를 먼저 한다. BIGINT 상한에서는 실제 상태 변경을 409로 거부하고 원자 rollback한다.
- publish DTO는 엄격한 `expected_metadata_revision`, `expected_document_revision`, `expected_publication_revision` 세 필드를 요구한다. 세 clock을 먼저 검사하고 검증된 현재 document와 title/summary/visibility·정렬 Tag ID/최초 표시명을 고정한다. meta/doc revision은 게시/취소로 변하지 않는다. 동일 source revision의 기존 publication은 최신 publication CAS를 만족할 때만 no-op이며 source revision이 바뀌었으면 같은 내용도 새 snapshot이다. unpublish는 `expected_publication_revision`만 받으며 현재 token과 같은 미게시 상태는 200 no-op이다.
- GET 기본 view는 현재 작성자에게 draft, 나머지는 publication이다. 명시 `view=draft/publication`을 허용하고 draft guard는 기존 작성자 전용으로 유지한다. optional Bearer는 기존 token 의존성을 사용하며 invalid/inactive token은 오류로 남고 API Key-only는 익명으로 취급한다. 공개 GET security에 익명 대안을 표시한다.
- draft 응답에는 현재 publication token/요약과 publish/unpublish capabilities를 추가한다. 공개 metadata는 별도 whitelist DTO로 snapshot 제목/요약/visibility/태그, source metadata/document revision, publication revision/시각만 제공하며 board_id/shelf_id/author_id는 현재 소속/SET NULL을 반영한다. 초안 제목·revision·timestamps·PII·스토리지 키는 노출하지 않는다. 공개 본문 revision은 snapshot source document revision이다.
- 공개 읽기는 현재 Board 상태/visibility·가입/제재·등급·현재 Shelf read_canvas 및 current/snapshot Canvas visibility의 교집합을 적용한다. 축소/이동은 즉시 제한하고 Canvas visibility 확대는 재게시 후에만 확대된다. 보관 Board는 읽기만, 정지는 404다. 현재 작성자가 명시 publication을 읽어도 같은 공개 권한을 적용한다.
- publication tag는 snapshot별 관계 테이블에 ID/표시명/순서를 저장하고 tag_id 역방향 인덱스를 두어 후속 공개 필터가 draft canvas_tags를 사용하지 않게 한다. 썸네일 필드/생성 worker는 추가하지 않는다.
- 공개 이미지 read는 같은 공개 가드와 현재 publication scope 참조가 있는 ready Asset에 한정한다. 작성자의 기본 draft read는 기존 미참조 ready 읽기를 유지한다. publish/unpublish/trash의 scope 교체는 기존 replace_refs로 draft/다른참조·TTL/outbox/fencing을 보존하고 파일 I/O는 트랜잭션 밖에서 수행한다.
- 현재 작성자/계정/멤버·Board/Shelf 정책과 metadata/document 기대 revision을 검사한 뒤 snapshot·상태/버전·publication 이미지 참조를 한 모델 트랜잭션에서 저장한다. 이후 편집은 초안만 변경한다.
- 타인 공개 읽기는 현재 Board/Shelf/등급/제재·Canvas 범위를 적용하고 metadata/태그/문서는 공개 snapshot에서 구성한다. 타 운영자/앱 관리자의 초안 접근은 허용하지 않는다. 공개 이미지도 현재 publication 참조로 제한한다.
- SQL·세션·잠금/트랜잭션·ORM 쓰기·driver 오류 변환은 모델에 유지하고 서비스/공유 가드는 DI 기반 정책/흐름을 소유한다. 별도 Repository 파일·서비스 간 private 호출을 추가하지 않는다.
- 기존 자식 데이터가 있는 SQLite/실제 PostgreSQL migration에서 Document/Asset/ref/Tag/outbox를 보존한다. User 삭제 SET NULL·unpublish/휴지통/복구·Board 삭제와 참조/정리 불변식을 연결한다.
- 목록/Plaza·cursor·썸네일 생성·개인 초안 목록·운영자 moderation·Canvas archive/자동 purge와 신규 UI는 후속이다.

# Verification Plan

- A 저장/게시→초안 수정→B 공개본 불변→재게시/취소, 현재 권한/등급/제재·private/members/익명·view/Token/API Key·metadata/태그/이미지 비밀 경계를 확인한다.
- SQLite/실제 로컬 PostgreSQL의 기존 데이터 migration·게시/CAS/저장/권한/정리 경쟁·flush/commit rollback과 임시 schema 제거를 검증한다.
- 계약·생성 타입과 한국어 문서를 마친 뒤 VERIFY_BASE=9cc741dfd43ef9c2571a7d598852a3a94384ebbe make verify-plan → make verify를 실행한다. 실제 선택 범위/재사용 정책을 따르고 훅을 우회하지 않는다.
- 실제 PR Type/라벨/ready/base/head/이슈 연결·PR governance까지 확인하고 부모 세션에 인계한다. main merge commit/최종 #51 종료는 부모가 담당한다. 검증된 동일 입력은 중복 실행하지 않는다.

# Impact

기존 작성자 전용 초안 API에 명시적 게시/공개본 열람을 추가한다. metadata/document CAS와 현재 Board/Shelf 권한을 유지하며 공개 GET 계약/보안 표기와 생성 타입을 함께 갱신한다. 신규 UI/운영 배포는 포함하지 않는다.

# Loop Alignment

요청/optional 읽기 또는 세션 쓰기 → 서비스 DI/현재 객체 정책 → 모델 트랜잭션/snapshot·참조/버전 → view별 최소 응답/계약 루프를 완성한다. 기존 파일 읽기는 SQL 잠금 밖에서 수행하고 정리 outbox 경계를 보존한다. UI/실시간/데스크톱 복구는 이번 범위가 아니다.

# Verification

- 초기 대상 검사: Canvas/Asset API·초안·이미지·공통 인증 inventory 195 passed / 59.52s. 새 엄격 revision/view 입력과 세션 POST/API Key 경계를 포함했다.
- 신규 publication SQLite: 첫 실행 23 passed / 1 failed / 19.92s. 실패는 Board DELETE 테스트가 기존 작성 헬퍼의 reason을 보내 엄격 DTO가422를 반환한 원인이었다. 테스트 요청을 실제 DELETE DTO로 고친 해당1개 재검사 1 passed / 1.41s. 추가 실제 API Key/invalid Bearer 및 기존 Tag migration 2 passed / 2.31s.
- 실제 로컬 PostgreSQL: CANVANITY_TEST_POSTGRES=1로 Board/Document/Tag/Publication 4 passed / 6.41s. 고유 schema의 이전 데이터 보존·JSONB·게시/취소/본문/metadata 경쟁, 현재 권한 회수의 실제 lock wait, 공유 읽기/권한 변경 양방향·취소/cleanup 양방향과 계정 삭제 SET NULL 경쟁을 확인하고 schema 삭제를 검증했다. 원래 DB/파일은 건드리지 않았다. 기본 full의 opt-in skip과 구분한다.
- 실제 개발 DB 사고: 사용자 DuplicateTable 보고 뒤 즉시 쓰기/새 검사 실행을 중단했다. 부모의 읽기 조사에서 revision0028와 빈 publication3테이블·초기 모델에 없던 position UNIQUE 누락을 확인했다. 원인은 모델→migration 파일 작성 사이 자동 reload의 migration 뒤 create_all 호출이다. 이 작업자는 실제 DB migration/수정을 실행하지 않았다. 부모는 version/새3테이블 잠금과 빈 행 재확인→고유 임시 schema의 현재 모델 DDL과 column/default/PK/FK/CHECK/index/unique 전수 비교→유일한 누락 position UNIQUE 추가→동일 schema 재검증/같은 transaction의 정확한0029 기록으로 복구했다. 전체 rollback 리허설 뒤 apply했고 기존13개 업무표 행수 불변·임시 schema 제거를 확인했다. 이후 정상 make db-migrate exit0과 db-current0029(head)를 확인했다. 부모가 실제 env/PG·Redis로 임시 loopback uvicorn을 기동해 /health/ready200과 database/redis ok, SIGTERM 뒤 Database/Redis/Storage 정상 정리·임시 서버 잔류 없음을 확인했다. 테이블/사용자 데이터 삭제나 blind stamp는 없으며 이력 우회/blind IF NOT EXISTS를 migration에 추가하지 않았다.
- 추가 startup 검사: 격리 SQLite에서 과거 create_all 순서의 DuplicateTable 재현과 새 startup의 pending 모델/이전 revision→정상 후속 migration, 기존 시작/종료·billing startup 57 passed / 1.33s. 공개 init_db API는 유지하고 앱에서 호출하지 않는다.
- 한국어 publication/domain/API/권한·초안/본문/이미지/태그/진입점·startup 문서와 양쪽 OpenAPI/생성 타입을 동기화했다. 모델이 SQL/잠금/트랜잭션/ORM 쓰기와 DB 오류를, 서비스가 DI/정책/흐름을 소유하며 라우터는 전송만 수행하는 경계를 수동 검토했다. 다른 서비스의 private 메서드 호출이나 별도 repository 파일은 없다.
- 최종 source의 PostgreSQL closure binding을 고친 뒤 신규 Publication 1개를 별도로 재확인해 1 passed / 2.37s였다. 기존 PG3개는 반복하지 않았다.
- 첫 루트 verify는 frontend contracts/openapi.json의 Prettier 형식에서 실패했다. 생성 타입/API 일치는 통과했고 같은 실행의 backend 전체는 1148 passed / 4 opt-in skipped / 283.04s였다. 프런트 JSON만 포맷해 제공자/소비자 JSON 값의 완전 일치를 확인했으며 루트 정상 receipt 정책으로 재실행한다. 수동 범위 강등은 하지 않는다.
- 최종 VERIFY_BASE=9cc741dfd43ef9c2571a7d598852a3a94384ebbe make verify-plan은 공유 인증/ORM/migration/startup/계약 영향으로 backend 전체·frontend full의15명령을 선택했다. 최종 make verify는 15 commands / 342.6s로 모두 통과했다(`.git/verification-logs/run-zoqzllq_`). JSON 포맷 수정으로 source 지문이 바뀌어 정상 정책이 재실행했으며 수동 강등/receipt 수정은 없었다.
- 최종 backend 1148 passed / PostgreSQL opt-in 4 skipped / 337.01s, frontend 209 passed, UI 250 passed, production18 passed, style-studio3 passed. 루트/프런트 하네스, 아키텍처·env/린트/계약, discovery/branding, 도구/설정·프로젝트 빌드·단일 패키징도 통과했다. 별도 실제PG4개+최종 Publication1개 성공과 기본 skip을 구분한다. UI/목록/운영 배포는 추가하지 않았다.
- 검증 순서 교훈: 양쪽 JSON을 명시 동기화한 뒤 소비자 JSON/생성 타입의 Prettier와 check-app 형식을 full 전에 확인해 의미 없는 포맷 실패와 전역 receipt 무효화를 피한다.
- 정상 staged/commit-msg/pre-push와 ready PR의 실제 metadata/governance를 확인한 뒤 부모에게 인계한다. 이 커밋 기록 시점의 원격 게시/병합 여부는 실제 GitHub PR을 기준으로 확인하며 main 병합/최종 #51 종료는 부모가 담당한다. 소스/문서/계약은 최종 성공 뒤 변경하지 않는다.

# State Ownership

프런트 런타임 변경 없이 계약/생성 타입만 동기화한다.

# Memoization

프런트 런타임 변경이 없어 해당하지 않는다.

# Performance Evidence

허용 문서/객체/이미지 한도와 짧은 잠금 경계를 유지한다. 처리량/부하 SLA를 주장하지 않는다.

# Page Family

## Family

신규 UI 변경 없음.

## Reference

기존 Board 정책·Canvas 초안/문서 CAS·Tag/이미지 계약.

## Shared Rules

한국어·단일 저장소·DI·모델의 DB 책임과 엄격 계약/생성 타입.

## Exceptions

없음. 세부 구현 계약을 구현 전에 확정한다.

## Evidence

새 화면 비교는 해당하지 않는다. 루트 계획이 선택한 기존 브라우저 회귀는 유지한다.
