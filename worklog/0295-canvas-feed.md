# Commit Title

feat: 공개 캔버스 목록과 커서 기반 관심사 태그 필터를 구현한다

# Changed File Scope

- Plaza/Board/Shelf의 공개 Canvas 목록 라우터·조회 서비스/공유 정책·모델 저장소·도메인 오류와 공유 운영 역할 상수. 기존 인덱스를 재사용하고 새 migration은 없다.
- SQLite/실제 격리 PostgreSQL·권한/페이지네이션/필터 회귀, 한국어 문서·양쪽 OpenAPI·생성 타입.

# Reason

#51/PR #52의 게시·공개본 단건 열람을 main 81b29f0에 반영했다. 같은 현재 권한으로 허용된 게시글을 Plaza/Board/Shelf에서 최신순 조회하고 공식 Interest/게시된 Tag로 찾을 수 있어야 한다. 신규 UI는 계속 보류하고 상위 #8/#24와 분리한 백엔드 완료 단위를 추적한다.

# Design

- 구현 전 확정 계약: `GET /canvases`는 optional `board_id`/`shelf_id`, 세 목록 공통 `interest_id`(공식 slug)/`tag_id`(UUID)/`limit`(기본20, 1..100)/`sort=latest`/`cursor`(최대2048)를 받는다. Board/Shelf 전용 경로는 공통 query만 허용하고 알려지지 않은 query는422다. 두 소속 필터는 AND이며 다른 Board의 Shelf 조합은404다. 문법이 유효하지만 없는/비활성 Interest·없는 Tag는200 빈 목록이다.
- `items`는 `CanvasPublicationInfo`의 공개 source clocks/게시시각과 snapshot `canvas` whitelist, 현재 `board`/`shelf`의 id·slug·name 및 `view=publication`만 가진다. `next_cursor`를 제공하고 total/본문/초안 revision·변경시각/PII·저장 키/사용 건수/작성 capabilities는 제공하지 않는다.
- Board scope와 전역 board_id는 현재 Board 읽기 가능 여부를 검사하고 읽을 Shelf가 없으면 빈 목록이다. Shelf scope와 전역 shelf_id는 현재 Board+read_canvas Shelf 정책을 검사한다. 없는/읽기 불가 scope는 같은 Canvas404다. is_visible=false는 권한을 바꾸지 않는다. optional Bearer가 잘못되면401이고 비활성/없는 계정은 기존 인증 계약 USER_NOT_FOUND404이며 API Key만 있으면 익명이다. 성공 Cache-Control은 private,no-store다.
- 저장소는 현재 활성 계정·scope 허용 여부, Board/Shelf/member/등급과 Board 기본/Shelf override의 read_canvas SQL, eligible publication header를 페이지화한 CTE와 정렬된 publication tags LEFT JOIN을 단일 SELECT statement로 읽는다. READ COMMITTED PostgreSQL의 statement MVCC 및 SQLite statement 읽기로 여러 Board의 현재 정책/header/tag 관계를 한 시점에 맞춘다. document JSONB와 ORM 전체 publication을 SELECT하지 않고 항목별 추가 조회를 하지 않는다. scope 상태도 같은 statement 결과에서 판정한다.
- 정렬은 published_at DESC, canvas_id DESC와 limit+1이다. next_cursor는 마지막 반환 item에서만 생성하고 sentinel/제한 row를 넣지 않는다. cursor payload는 v=1/domain=canvas-publication-feed/route scope/plaza의 소속 필터를 포함한 canonical SHA-256 filter_hash/sort=latest/UTC RFC3339 시각/UUID만 허용한다. strict 타입·JSON 중복 key/extra·base64url canonical encoding/길이·날짜를 검사하고 다른 경로 scope/filter 사용은422 CANVAS_INVALID_CURSOR다. limit 변경은 허용한다. unsigned cursor는 권한이 아니며 매 조회 현재 권한을 다시 적용한다.
- 새 게시/재게시는 최신 시각 위치에 나타나고 초안 저장은 정렬·snapshot 태그를 바꾸지 않는다. 게시 취소/휴지통/현재 권한 상실은 다음 조회에서 제외되며 Shelf 이동은 현재 소속/정책에 바로 반영한다. 여러 요청 사이 완전한 시간 고정 pagination은 보장하지 않는다. 기존 ix_canvas_publications_published·게시태그(tag_id,canvas_id)·Board/Shelf/회원/정책 PK/FK 인덱스를 사용하고 추가 migration은 실제 SQL/계획에서 필요한 근거가 있을 때만 도입한다.
- #51 현재 Board/Shelf/멤버·등급/제재와 current/snapshot visibility·게시 존재 조건을 동일하게 적용한 row 집합을 정렬/필터/페이지네이션한다. 제한 row를 limit 뒤 걸러 제목/ID/cursor를 노출하거나 누락 페이지를 만들지 않는다.
- 공식 Interest는 현재 Board 연결, 자유 Tag는 고정 publication tag로 필터링한다. 초안 제목/태그/본문 수정은 재게시 전 공개 결과에 영향을 주지 않는다. 목록 header/태그/현재 관계를 항목별 쿼리 없이 일관되게 읽는다.
- cursor의 도메인/scope/정렬·필터/UTC 시각/UUID와 크기·입력 형태를 엄격히 검증하고 각 페이지에서 현재 권한을 재적용한다. 완전한 시간 고정 snapshot 페이지네이션을 주장하지 않는다.
- SQL/세션/조회·ORM/driver 오류 변환은 모델이 소유하고 서비스/가드는 DI·정책/흐름을 담당한다. 별도 Repository 파일·서비스 DB 호출·타 서비스 private 호출을 추가하지 않는다.
- 새 테이블/인덱스가 필요하면 근거 기반 최소 migration과 기존 데이터 보존을 검증한다. startup은 Alembic만 사용하며 create_all을 호출하지 않는다.
- 신규 UI·Board 홈 동적 widgets/레이아웃·개인 초안 목록·썸네일/인기순/추천·moderation/Canvas archive·댓글/좋아요/구독은 후속이다.

# Verification Plan

- SQLite/실제 PostgreSQL의 여러 Board/Shelf·동일 게시시각 tie/cursor·필터/초안 비노출·현재 역할/등급/제재/범위/수명주기와 단건 공개 읽기 parity를 확인한다.
- 목록이 JSONB 본문을 로딩/노출하지 않고 header/태그가 일관된 snapshot이며 제한 row가 cursor에 영향을 주지 않는지 검증한다.
- 양쪽 계약/타입과 JSON/TS Prettier/값 일치를 전체 검사 전에 확인한다. VERIFY_BASE=81b29f0a2fcc3ab1518ec5b5b2f2b541dd075e7c make verify-plan → make verify를 정상 범위/receipt 정책으로 실행한다.
- 정상 거버넌스/commit-msg/pre-push와 ready PR 실제 타입/라벨/head/관련 이슈·PR governance 및 merge commit을 확인하고 하위 이슈를 종료한다.

# Impact

새 공개 목록 API를 추가한다. 기존 단건/작성자 초안·게시/이미지/계정·공식 Interest 계약을 보존한다. UI 런타임/운영 배포는 포함하지 않는다.

# Loop Alignment

optional 읽기 요청 → 서비스 DI/현재 scope 정책 → 모델의 권한 적용 SQL/keyset·snapshot header/tag → 최소 DTO/cursor/계약 루프다. 관계형 DB/오류 경계는 모델에 두고 UI/실시간/worker·데스크톱 복구는 변경하지 않는다.

# Verification

- 실제 대상 검사: API70개와 SQLite 통합2개 통과(72 passed, 4.07s). 새 HTTP 검사의 imported fixture 의존성 누락을 고친 뒤 해당 검사1개 통과(1.93s). 초기 API 검사에서 strict datetime before-validator 변환과 기존 USER_NOT_FOUND404 기대를 수정했다. SQLite 수명주기 fixture는 일반 회원이 쓸 수 없는 공지 Shelf 대신 같은 Board 일반 Shelf로 바꿨다. 실패를 성공으로 집계하지 않았고 최종 루트 검사는 최종 소스 전체를 확인했다.
- 실제 PostgreSQL: CANVANITY_TEST_POSTGRES=1의 Board/Tag/Document/Publication/Feed 5개 통과(10.03s). 각각 localhost 고유 schema에 migration/데이터를 격리하고 제거를 재검증했다. 원래 개발 DB/파일 변경은 없으며 새 migration도 없다. 피드 검사는 같은 SQLite 권한 행렬/keyset/다중태그/수명주기, 단일 statement 결과 뒤 별도TX 재게시·visibility축소의 old header/tag 일관성 및 다음 읽기 회수를 검증했다. EXPLAIN은 .git/canvas-feed/postgres-plan.json에 보존한다.
- 사전 계약 검증: contract-export→frontend 명시 복사→frontend-api-generate, JSON/생성TS Prettier write/check, 양쪽 JSON 값 동일·세 GET의 anonymous security/query whitelist 확인, make contract-check frontend-api-check frontend-typecheck 통과. backend-architecture-check와 검사기4개 통과.
- 최종 루트: VERIFY_BASE=81b29f0a2fcc3ab1518ec5b5b2f2b541dd075e7c make verify-plan→make verify가 backend 전체/frontend full과15개 명령을 선택했다. 최종 실행은101.4s에 모두 성공했다(.git/verification-logs/run-nu6df8jr, 종합 .git/canvas-feed/verify-user-resume.log). 정상 정책의 유효한 동일 입력/출력 receipt11개를 재사용했고4개를 실행했다. 마지막 격리 브랜드 구성 빌드54.9s(단위209개·프로덕션18개 포함)와 통합 패키징0.4s까지 완료했다.
- 전체 선택 범위의 실제 성공: backend1221개/실제PG opt-in5개 skip(477.80s), frontend 단위209개, 일반 UI250개, production18개, style-studio3개. 별도 opt-in PG5개/10.03s 성공과 기본 검사 skip을 구분했다. 신규 UI는 없어 별도 신규 화면 비교를 추가하지 않았고 루트가 선택한 기존 전체 브라우저/도구/브랜딩·계약·거버넌스 회귀는 생략하지 않았다.
- 환경 실패와 재개: 첫 style1440의30초 제한이10.6분 뒤 종료됐고 입력창은 실패 screenshot에 정상 존재했다. 실제 전원 로그의2026-11-03 21:41:13 Maintenance Sleep639초→21:51:52 DarkWake와 일치했다. 같은 입력/소스/timeout에서 해당 검사1개가 각성 상태3.2s(테스트2.1s)에 통과했다. 이후 격리 구성 빌드의 useAdminUsers5초 제한이92.186초 뒤 실패한 구간도2026-11-04 06:13:57 Sleep94초→06:15:31 DarkWake와 일치했고, 대상은121ms(전체921ms)에 통과했다. 다음 한정 시도의 useKeyboardShortcuts121.572초/worker timeout도09:08:35 Sleep123초→09:10:38 DarkWake와 겹쳐 재시도를 중단하고 사용자 재개를 기다렸다.
- 사용자 명시 재개 뒤 실행 프로세스 수명에만 caffeinate -diu를 적용하여 위 최종 정상 검증을 완료했다. 제품/테스트/timeout/검증 범위·receipt를 바꾸거나 다른 프로세스를 종료하거나 영구 OS 설정을 변경하지 않았다. 초기 실패를 전체 성공으로 설명하지 않는다.
- 완료 시 수동 책임 검토: 라우터는 query/응답/헤더와 서비스 호출만 담당하고 서비스는 DI·cursor·도메인 scope 결과만 사용한다. 모델이 단일 SQL·세션·DB 오류 변환을 직접 소유한다. 타 서비스 private 호출·세션 전달·SQL 예외/제약 해석 우회가 없으며 일반 app 전역 역할/API Key를 Board 권한으로 쓰지 않는다.
- 정상 staged/commit-msg/pre-push·ready PR 실제 메타데이터/거버넌스는 이어지는 게시 단계에서 확인하고 이슈/PR에 기록한다. main 병합·이슈 종료는 부모 세션이 맡으며 완료 예정으로 기록하지 않는다.

# State Ownership

프런트 런타임 변경 없이 계약/생성 타입만 동기화한다.

# Memoization

프런트 런타임 변경이 없어 해당하지 않는다.

# Performance Evidence

SQLite/실제 PostgreSQL에서 제한 행을 정렬/limit 전에 제거하고 다중 태그가 page 경계를 늘리지 않는 것을 확인했다. DB event로 SELECT 1개·본문/초안 tag 미선택을 검사했고 실제 PG EXPLAIN과 기존 정렬/Tag/Board-Shelf 인덱스 존재를 확인했다. 소형 fixture의 계획은 대용량 처리량/scan SLA 근거가 아니며 측정 기반 새 인덱스 요구가 없어 기존 인덱스를 재사용했다.

# Page Family

## Family

신규 UI 변경 없음.

## Reference

기존 Board 목록·Canvas publication·권한/태그 계약.

## Shared Rules

한국어·단일 저장소·DI·모델 DB 책임과 계약/타입 동기화.

## Exceptions

없음. 구현 전에 확정한 조회/페이지네이션 계약을 따른다.

## Evidence

신규 화면 비교는 해당하지 않는다. 루트가 선택하는 기존 회귀는 유지한다.
