# Commit Title

feat: 보드 공식 홈 레이아웃 저장과 권한별 위젯 조회를 구현한다

# Changed File Scope

- Board 공식 layout 관리/저장·방문자 홈 widget projection/data, 모델/서비스·공유 가드·라우터/오류와 필요한 최소 migration.
- API/SQLite/실제 격리 PostgreSQL·권한/CAS/보존 회귀, 한국어 문서·양쪽 OpenAPI·생성 타입.

# Reason

공개 Canvas 목록 #53/PR #54를 main 9006c9d에 반영했다. 운영자가 공식 배치를 저장하고 방문자는 현재 권한으로 허용된 데이터만 볼 수 있어야 한다. 상위 #25의 제품 UI와 분리한 백엔드 단위 #55를 완료한다.

# Design

- 구현 전 현재 기본 layout/기존 schema와 위젯별 허용 필드/source·좌표/크기·문서/요청 byte 제한을 확정한다. UI widgets와 Content Canvas nodes/edges를 구분한다.
- 공식 GET/PUT은 현재 active Owner/Admin 역할로 검사하고 활동 등급은 편집 권한으로 사용하지 않는다. layout revision의 독립 CAS/no-op/stale/overflow와 최소 감사·Board revision 관계를 구현 전에 명시한다.
- 방문자 home은 저장 문서와 현재 widget 데이터를 구분하고 제한 Shelf source 위젯의 ID/이름/config도 방문자 projection에서 숨긴다. 운영자 관리 GET은 전체 설정을 제공하지만 본문 읽기 권한을 추가하지 않는다.
- collections는 현재 방문자가 읽을 수 있는 공개 snapshot header/Tag만 사용하며 초안·제한 콘텐츠/관계를 노출하지 않는다. navigation의 숨김/읽기 정책, 현재 Board 소개와 cover 없음/null을 명확히 한다. 중복 source/N+1/본문 JSONB 로딩을 피한다.
- SQL·세션·잠금/트랜잭션·ORM 쓰기·driver 오류 변환은 모델에 유지하고 서비스는 DI/현재 정책/흐름만 담당한다. 별도 Repository 파일·서비스 DB 호출·다른 서비스 private 호출을 추가하지 않는다.
- 기존 layout revision INTEGER32와 API/목표 상한을 맞추는 최소 변경을 선택하고 필요시 기존 자료가 있는 SQLite/실제PG migration을 검증한다. startup은 Alembic만 사용한다.
- 신규 UI·개인화 layout/카메라·Profile/Plaza 배치·Board 미디어 업로드/썸네일·소셜·공동 편집은 후속이다.

구현 착수 전 확정한 계약(인계 후 root 보고/검토): schema_version=1, 위젯 ID는 ASCII 영숫자로 시작하는 영숫자/밑줄/하이픈 1~80자, 전역 중복 거부다. 위치는 엄격 유한수 ±100,000, 크기는 각 축 양수~100,000이다. board_intro/board_cover/shelf_navigation에는 source를 허용하지 않고 canvas_collection만 현재 Board UUID·선택 Shelf UUID(생략/null=Board 전체)·latest·limit1~20을 받는다. 100widgets/정규 UTF-8 256KiB와 파싱 전 envelope 256KiB+4KiB 상한을 적용한다.

기존 INTEGER32를 그대로 사용하고 API 상한0~2147483647을 맞춰 새 migration은 만들지 않는다. stale를 동일문서보다 먼저 거부하며 canonical no-op은 revision/감사 모두 유지한다. 실제 변경은 layout revision만+1, Board revision은 불변이고 포화 변경은409다. 최소 감사는 이전/새 revision과 canonical SHA256·위젯 수·reason만 저장한다.

관리 조회/저장은 Board 잠금→활성 계정 공유 잠금→현재 멤버 역할→layout 잠금 순서다. active Owner/Admin만 허용하고 archived는GET만 허용한다. 방문자 읽기는 모델 소유 PG REPEATABLE READ READ ONLY 또는 SQLite 명시BEGIN에서 계정·Board·멤버·정책·레이아웃·metadata-only ranked collection+고정태그 batch를 읽는다. 최대100개 source를 중복 제거하고 각 source당 최대20개를 한 SQL로 제한한다. 숨김 Shelf도 읽기 source로 사용할 수 있으나 메뉴에는 표시하지 않는다. 제한/삭제된 Shelf source의 위젯은 방문자에게 ID/config까지 모두 생략하고 관리GET은 남은 설정을 반환해 수정 가능하게 한다. Cover 미디어는null이다.

# Verification Plan

- widget/source/바이트·역할/등급 분리·방문자 projection·current policy/snapshot·저장/재조회·no-op/충돌/실패·최소 감사와 기존 문서 보존을 검증한다.
- SQLite와 실제 고유 schema PostgreSQL에서 schema/JSONB·CAS 단일 승자·권한 회수 lock wait·rollback/기존 데이터와 삭제 경계를 확인한다. 원래 DB/파일·환경은 보존한다.
- 계약/타입·양쪽 JSON 값과 JSON/TS 형식을 먼저 확인한 후 VERIFY_BASE=9006c9dd38f37e70b08a00a62940a147cd96ce4d make verify-plan → make verify를 정상 범위/receipt로 실행한다.
- 정상 staged governance/commit-msg/pre-push와 ready PR 실제 타입/라벨/base/head/이슈·PR governance, merge commit/main 동기화 뒤 하위 이슈를 닫는다.

# Impact

공식 layout 저장/관리 API와 방문자 home 응답을 확장한다. 기존 기본 문서와 공개 조회/회원 권한·계정/게시글 데이터를 보존한다. 제품 UI·운영 배포는 포함하지 않는다.

# Loop Alignment

요청/운영자 인증 또는 방문자 읽기 → 서비스 DI/역할·현재 정책 → 모델 CAS·문서/감사 또는 현재 header/위젯 source → 관리/방문자 DTO/계약 루프를 따른다. 개인 카메라/UI·실시간/worker/데스크톱 복구는 변경하지 않는다.

# Verification

- 사전 확정한 계약대로 관리 GET/PUT, typed 방문자 projection/widget_data, 모델 내부의 중복 source 제거/ranked batch와 독립 layout revision/최소 감사를 구현했다. source/본문 SQL과 세션은 모델이 소유한다. 공통 구조 관리 가드로 Shelf/layout 정책의 의미를 분명히 했다.
- 기존 Board API/개설/공개 feed의 좁은 회귀 17개가 통과했다. 신규 API 스키마 36개, SQLite 통합 1개, 실제 HTTP 인증/감사/slug 별칭 1개, 실제 PostgreSQL 격리 schema 통합 1개로 총 39개가 통과했다. 로그는 `.git/board-layout/targeted-final.log`다.
- 신규 39개 중 실제 PostgreSQL 검사 1개는 별도로 명시 실행해 통과했다. migrations head0029/JSONB, 기존 Canvas/document/publication/Tag/Asset/ref/outbox 보존, CAS 단일 승자, pg_blocking_pids로 입증한 권한 회수 lock 대기, 동시 layout/publish/policy/account 변경 중 RR READ ONLY snapshot 일관성을 확인했다. 생성한 schema를 정리했고 원래 개발 DB/env/파일은 변경하지 않았다.
- 실패 주입으로 flush/commit 이전 SQLAlchemyError의 문서/revision/감사 원자 롤백을 확인했다. 실제 commit 결과가 불명확한 네트워크 장애의 강제 복구를 주장하지 않으며 관리 GET/revision 재확인 계약을 문서화했다. 초기 targeted 실패는 계정 오류의 우선순위 기대, SQL alias 계수 범위, fixture의 Canvas→Shelf 삭제 flush 순서와 상한 테스트의 UUID import를 바로잡았다. 제품 권한/timeout/검증 범위는 완화하지 않았다. 최종 39개에는 기존 Pydantic/argon2 경고만 남았다.
- 양쪽 OpenAPI 값 동등성, backend export 최신성/pinned consumer 호환, 생성 타입 일치, TypeScript typecheck와 consumer JSON/TS Prettier가 통과했다. provider JSON은 exporter의 indent2/정렬 형식, consumer JSON은 기존 Prettier indent4를 유지한다. 처음 provider까지 Prettier를 적용해 바이트 기준 검사가 실패했으므로 정상 export로 복구하고 값 동등성과 두 형식을 재확인했다.
- 최종 source/계약/문서 검토 승인 뒤 최초 루트 plan은 31개 파일의 공유/불명 영향으로 전체 15개 명령을 선택했다. frontend UI 250개와 나머지 선행 그룹은 통과했지만 backend는 1,258개 통과/6개 생략/1개 실패(531.91s)였다. 로그는 `.git/board-layout/full-verification.log`, `.git/verification-logs/run-h0f42m_c/2.log`다.
- 유일한 실패는 기존 `test_openapi_session_only_inventory_is_explicit`의 명시된 세션 전용 API 목록에 새 layout GET/PUT이 빠진 테스트 계약 누락이었다. 실제 set diff는 정확히 두 경로였고 제품 인증 회귀는 없었다. 검토 후 expected 집합에 두 경로만 추가하고 신규 HTTP 회귀에서 유효 문서/실제 API Key의 PUT 401 거부를 더했다. 두 종속 검사가 통과했다(`.git/board-layout/auth-inventory-final.log`). 검사 완화나 제품 source/계약/환경/timeout/receipt 수동 변경은 없다.
- 최종 테스트 diff도 재검토 승인을 받았다. 정상 plan→verify가 실패 backend 그룹을 다시 실행하고 내용이 같은 8개 그룹의 성공 receipt를 재사용했다. 최종 루트 검증은 15개 명령 모두 통과(319.2s, jobs=2)했다. backend는 1,259개 통과/6개 생략/기존 경고 36개(312.86s)였다. frontend 단위 209개, UI 250개, production 18개, style-studio 3개의 정상 결과와 계약/패키징도 확인했다. 로그는 `.git/board-layout/full-verification-final.log`, `.git/verification-logs/run-49ok9oxx`다.
- full에서 생략한 6개는 명시 실행이 필요한 PostgreSQL 검사다. 이번 신규 PostgreSQL 검사 1개는 위 39개 묶음에서 실제 실행해 이미 통과했고 fixture/feature source가 바뀌지 않아 중복 실행하지 않았다. 실제 제공자 호출, 운영 배포, 새 UI, 개인 배치와 미디어 연결은 요청 범위 밖이다. 기존 UI/production 회귀는 정상 계획대로 완료했다.
- source/계약/문서/최종 테스트 diff 검토와 정상 staged 거버넌스가 통과했다. commit-msg/pre-push 훅, ready PR와 실제 PR 거버넌스 확인을 이어간다. 병합/이슈 종료/main 동기화는 최종 검토 후 root가 담당한다.

# State Ownership

프런트 런타임 변경 없이 계약/생성 타입만 동기화한다.

# Memoization

프런트 런타임 변경이 없어 해당하지 않는다.

# Performance Evidence

100개 위젯이 같은 source를 재사용하는 실제 SQLite/PG 홈에서 위젯당 20개·총 2,000개 header 상한과 정렬을 검증했다. 고유 source는 최대 100개, batch SQL은 요청당 1개이며 본문 미조회/중복 source 제거를 관측했다. 처리량 SLA는 주장하지 않는다.

# Page Family

## Family

신규 UI 변경 없음.

## Reference

기존 Board 기본 홈·Shelf 정책·공개 Canvas feed 계약.

## Shared Rules

한국어·단일 저장소·DI·모델 DB 책임·계약 동기화.

## Exceptions

없음. 세부 관리/방문자 계약은 구현 전에 확정한다.

## Evidence

새 화면 비교는 해당하지 않는다. 루트가 선택한 기존 회귀는 유지한다.
