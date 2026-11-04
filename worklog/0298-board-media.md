# Commit Title

feat: 보드 대표 이미지와 커버를 연결한다

# Changed File Scope

- Board 미디어 모델/참조·최소 migration·현재 권한/DTO/DI 서비스·라우터와 기존 outbox/worker·Board 종료 연계.
- API/SQLite/실제 격리 PostgreSQL/임시 파일 검증, 한국어 문서·양쪽 계약·생성 타입.

# Reason

Board 기본 운영·공식 홈·내 Canvas 목록이 main에 반영됐지만 대표 이미지/커버는 연결되지 않았다. 상위 #22에서 백엔드 하위 #59를 분리해 Board 소유 미디어와 현재 권한·파일 정리를 구현한다.

# Design

- 구현 전에 경로/전송·슬롯/현재 참조/응답·한도·revision/no-op/stale/포화·감사와 잠금/읽기·파일 I/O/outbox 계약을 확정한다.
- Canvas assets의 필수 소속/FK를 유지하고 Board 전용 미디어 소유와 ready 현재 참조를 DB에서 보장한다. 참조 많은 기존 부모 테이블 재생성을 피하는 최소 migration을 실제 head 다음에 둔다.
- 현재 active Owner/Admin만 변경하고 읽기는 현재 계정/Board/member 정책을 적용한다. 활동 등급과 운영 역할은 분리한다.
- 기존 ObjectStorage·안전한 이미지 검증/정규화와 내구성 있는 outbox/worker를 필요한 만큼 재사용한다. pending/outbox를 put 전에 예약하고 I/O는 잠금 밖에서 수행하며 ready 직전 현재 권한/revision을 재검사한다.
- 실패/취소/불명확한 commit·교체/제거·Board 삭제/늦은 put에서도 현재 ready 참조를 보상 삭제하지 않고 기존 데이터/파일·lease/fencing/위치 경계를 보존한다.
- Board 목록/상세/홈의 요약과 실제 cover widget 데이터를 연결하되 저장 layout과 Canvas clocks는 바꾸지 않는다. 임의 Asset/외부 URL 입력·N+1·서비스 DB 호출을 추가하지 않는다.
- 신규 UI/크롭 편집기·썸네일·개인 문서·소셜·제공자 설정/운영 배포는 후속이다.

## 구현 전 확정 계약

- `0030_board_media`는 새 `board_media_assets`, `board_media_refs`만 생성한다. 기존 boards/assets/outbox를 ALTER/재생성하지 않는다. assets에는 Board FK(RESTRICT), 업로더 FK(SET NULL), slot avatar/cover, private key/location/fingerprint/hash, 실제 image/webp 바이트/크기/프레임, pending/ready/deleting·1시간 deadline을 둔다. `(board_id, slot, id, state)` UNIQUE와 refs의 동일 복합 FK·`asset_state='ready'` CHECK로 같은 Board·slot·ready만 선택한다. refs PK는 `(board_id,slot)`, asset_id 인덱스와 assets uploader/Board 선두 인덱스를 둔다. Canvas의 canvas_id/기존 FK는 그대로다.
- outbox 컬럼은 바꾸지 않는다. 불변 키 `board-media/{asset UUID}/{random 32hex}.webp`와 기존 canvas-assets namespace로 등록부를 라우팅한다. 모델은 실행 시 local import로 순환을 피하고 Alembic/worker/test metadata에 두 새 모델을 등록한다. claim/finish/upload_failed는 Board→해당 Asset→outbox 순서이며 Board 삭제는 Board→Board media UUID 오름차순→해당 outbox→Canvas assets 기존 순서다. 선택 변경은 Board→active User SHARE→새/이전 media UUID 오름차순→outbox 순서다. 모든 파일 I/O는 트랜잭션 밖이다.
- PUT `/api/v1/boards/{board_id}/media/{slot}`는 multipart `file`, `expected_revision`, `reason`을 받는다. slot은 avatar/cover enum, reason은 trim 후 1..500자다. revision은 JSON DELETE에서는 strict int, multipart에서는 ASCII 십진 문자열만 허용하고 bool/float/음수/부호/공백/2^31-1 초과를 거부한다. DELETE는 같은 경로의 JSON form, GET은 `/media/{slot}/{asset_id}` 버전 경로다. 쓰기는 세션 전용, GET은 optional Bearer(API Key만 있으면 익명)다. 응답은 board_id/slot/media/board_revision/changed이며 summary는 id/content_type/byte_size/width/height/frame_count/created_at/상대 API URL만 제공한다.
- 현재 active 계정·해당 active Board의 active Owner/Admin만 변경한다. Moderator/활동등급/전역admin/다른 Board 운영자는 별도 권한이 없다. 읽기는 현재 active 계정(로그인 시)·Board.check_read와 선택된 ready version을 같은 snapshot에서 확인하며 private 비회원/제재/정지/타 Board·slot/Canvas/pending/deleting/구버전은 404다. 저장소 I/O 뒤 현재 선택/정책을 다시 snapshot 확인한다. archived 읽기는 유지한다. 정상 파일만 hash/size/MIME/location 확인 후 image/webp·private,no-store·nosniff로 반환한다.
- Board INTEGER32 revision을 공용 CAS로 사용한다. 사전검사·예약·최종 ready에서 expected 값을 확인한다. 예약은 Board clock/선택/감사를 바꾸지 않으며 최종 ready+현재 ref 교체+이전 삭제 예약+media_changed 감사가 원자적으로 revision +1 한다. 같은 내용도 새 UUID 교체다. 동시 같은 revision 업로드는 하나만 성공한다. 중간 설정/권한 변경은 최종검사에서 거절한다. 빈 슬롯 DELETE는 기대값 검사 뒤 changed=false·clock/감사 무변경, stale는 409, 변경 시 2^31-1 포화는 409다. layout/document/publication clock은 유지한다. 감사는 slot/이전·새 ID/전후 revision/reason만 저장·typed whitelist로 조회한다.
- 사전 권한/CAS 확인→입력 최대8MiB 읽기→기존 안전한 PNG/JPEG/WebP/GIF 실제 디코드/EXIF 보정/메타 제거 WebP 정규화(출력8MiB·누적16M pixels·100frames)→재검사/예약 commit→put→최종 재검사/ready commit 순서다. Board별 pending 최대8개, 전체 등록 최대200개(삭제 대기 포함)다. 파일명/MIME은 신뢰하지 않는다. put 전 parentless outbox를 같은 tx에서 예약한다. 실패/취소는 shield 정리 의도를 유지하고 현재 confirmed ready는 불명확 commit 보상에서 삭제하지 않는다.
- 교체·제거된 ready는 즉시 미선택/deleting·삭제 outbox, pending 실패/Board 삭제는 원래 deadline과60초 settle을 지켜 늦은 put을 수습한다. 기존600초 lease/fencing·5회 retry/backoff·blocked/dead/done tombstone 재예약을 유지한다. worker claim은 strict key/해당 등록부 asset UUID/Board/key/fingerprint 일치 및 두 등록부의 같은 key/fingerprint와 Canvas draft/publication·현재 Board ref·프로필 생존 참조를 검증한다. 오염된 key/소속/location은 파일 삭제 전에 blocked다. uploader 삭제는 SET NULL이고 소유권 이전은 미디어를 유지한다.
- BoardSummary는 `avatar_asset_id`, `cover_asset_id`, `avatar`, `cover`를 현재 refs에서 제공한다(boards soft UUID 컬럼을 추가하지 않는다). 목록은 기존 필터/계정/Board/revision/Interest와 media batch를 PG RR READ ONLY/SQLite BEGIN snapshot으로 묶고 N+1을 만들지 않는다. 상세/by-slug/home은 기존 snapshot에 batch media를 포함하고 생성/설정 응답은 같은 tx에서 조회한다. home의 board_cover.media는 동일 summary.cover이며 저장 layout과 임의 source/asset/url 금지는 유지한다. home capabilities에 can_manage_media를 현재 Owner/Admin·active Board/계정 기준으로 제공한다.
- downgrade는 새 등록/선택 또는 board-media outbox 기록이 하나라도 남으면 거부하고 자료를 보존한다. 신규 자료가 빈 경우에만 두 새 테이블을 제거한다. migration29 자료·outbox 비어있지 않은 보존과 FK 활성 SQLite/고유 PostgreSQL schema 왕복을 검증한다. 원본 개발 DB/env/files에는 직접 migrate/repair/stamp를 실행하지 않는다.

# Verification Plan

- 역할/등급/상태·public/private·현재 참조/이전 버전·인증 inventory/API Key·파일 검증/한도·CAS/no-op/감사/실패를 확인한다.
- FK 활성 SQLite/실제 고유 schema PostgreSQL의 migration 보존·동시 교체·권한 회수·삭제/cleanup 경계와 임시 실제 LocalStorage/CLI의 업로드→조회→교체/제거→정리를 검증한다.
- 원래 DB/env/파일·Canvas/프로필·다른 Board·outbox/lease를 보존한다. PostgreSQL 설계 스킬의 FK 인덱스·잠금 순서·짧은 트랜잭션 기준을 현재 구조에 적용한다.
- 양쪽 OpenAPI 값/각 형식·생성 타입/TypeScript를 먼저 확인하고 VERIFY_BASE=3a67a4185d7278e3ccc368def4c919ec4ae509c2 make verify-plan → make verify를 정상 범위/receipt로 수행한다.
- 정상 staged governance/commit-msg/pre-push·ready PR 실제 메타데이터/거버넌스·merge commit/main 동기화 후 하위 이슈를 닫는다.

# Impact

Board 소유 미디어·안전한 현재 이미지 API·정리 수명주기를 추가한다. 기존 Canvas Asset/프로필·문서/태그·레이아웃·개발 환경을 보존하고 스키마/계약은 같은 변경에서 이관한다.

# Loop Alignment

요청/현재 운영·읽기 권한 → DI 서비스의 검증/파일 I/O 흐름 → 모델의 pending/참조/CAS/감사/outbox → guarded bytes/요약·worker 재시도 루프를 따른다. 신규 UI·실시간/데스크톱 복구는 변경하지 않는다.

# Verification

구현 전 위 계약을 확정하고 root의 source 시작 검토를 받은 뒤 구현했다. 완료 checkpoint/전체 검증/게시 결과는 아래에 구분한다.

- 수동 책임 검토: 새 라우터는 bounded multipart/응답만 처리하고, BoardMediaService는 현재 권한/CAS·순수 정규화·스토리지 I/O를 조합한다. 모든 SQL/ORM 저장 필드·트랜잭션/오류 변환은 models에 유지했다. 서비스 간 private 호출과 임의 provider client 생성은 없다. 공개 pure normalize_canvas_image를 재사용했다.
- 정적 사전 검사에서 모델 Literal/Annotated alias의 router import가 기존 architecture 규칙에 걸렸다. slot은 StrEnum으로, ASCII multipart/텍스트 scalar 검증은 순수 form_fields 유틸로 옮겼고 checker 규칙은 바꾸지 않았다.
- 실패 보상 후 pending이 deleting이 된 경우의 Board 삭제가 기존 upload grace를 앞당길 수 있는 경계를 발견했다. 공용 enqueue의 Board 삭제 경로만 기존 upload_pending/upload_failed deadline/settle을 보존하며 Canvas/Board 양쪽 실패→삭제→늦은 put 검증을 추가했다. 정상 ready 교체/제거의 즉시 정리와 tombstone/lease는 유지한다.
- 초기 API prefix/기존 inactive HTTP404 기대값 두 테스트 오류를 실제 계약에 맞췄다. 이후 광범위 targeted143개(81.65초), 신규/기존 실제 PostgreSQL8개(14.37초)가 통과했다. 이후 grace/전송 타입 보강의 최종 영향 검사를 별도로 진행한다. 원본 개발 DB/env/파일에는 직접 migrate/repair/stamp를 하지 않았다.
- 실제 임시 LocalStorage/SQLite HTTP·CLI와 실제 PostgreSQL schema/파일을 구분했다. 외부 S3/R2/Supabase 제공자·실제품 UI/운영 배포는 실행하지 않는다.

## 완료 checkpoint

- 최종 영향 targeted105개 통과(68.45초): strict enum/multipart/400·API Key inventory/실제 거부·현재 권한/CAS/파일/감사·SQLite 0029 보존·Canvas 공용 cleanup/CLI·실패 grace를 확인했다. `.git/board-media/checkpoint-targeted.log`.
- 실제 PostgreSQL8개 통과(14.14초): 신규 media와 기존 Board/Tag/문서/게시/feed/home/self-list probe. Board/User의 실제 pg_blocking_pids 대기, 동시 업로드 단일 승자, 업로드↔Board삭제·cleanup↔삭제 양방향, expired claim/late put/tombstone·FK/rollback·RR batch 일관성과 schema 정리를 확인했다. `.git/board-media/checkpoint-postgres.log`.
- backend-check/architecture-check, 양쪽 OpenAPI 값 동등·contract-check/frontend-api-check/frontend-typecheck와 consumer JSON/TS Prettier 통과. schema alias는 checker 변경 없이 Enum/순수 전송 유틸로 정리했다. `.git/board-media/static-final.log`, `checkpoint-contracts.log`, `checkpoint-format.log`.
- root의 소스/문서/계약/targeted checkpoint 읽기 검토와 full 진행 승인을 받았다. 기준 main의 정상 verify-plan→verify를 이어 수행하며 아직 커밋/PR/병합은 하지 않았다.

# State Ownership

프런트 런타임 변경 없이 계약/생성 타입만 동기화한다.

# Memoization

프런트 런타임 변경이 없어 해당하지 않는다.

# Performance Evidence

바이트/파일·참조 한도와 batch/잠금/파일 I/O 경계를 검사하며 처리량 SLA를 주장하지 않는다.

# Page Family

## Family

신규 UI 변경 없음.

## Reference

기존 Board 운영/공식 홈·Canvas Asset·ObjectStorage/cleanup 계약.

## Shared Rules

한국어·단일 저장소·DI·모델 DB 책임·파일 I/O 분리·계약 동기화.

## Exceptions

없음. 세부 소유/전송/정리 계약을 구현 전에 확정한다.

## Evidence

새 화면 비교는 해당하지 않는다. 루트가 선택한 기존 회귀는 유지한다.


## 전체 검증·환경·게시 경계

- `VERIFY_BASE=3a67a4185d7278e3ccc368def4c919ec4ae509c2 REDIS_IN_MEMORY=true make verify-plan`은43파일과 backend complete suite/frontend full·전체15명령을 선택했다. 동일 환경의 `make verify`는397.1초에15명령 모두 통과했다. 로그: `.git/verification-logs/run-rkp78wq0`, `.git/board-media/full-verification.log`.
- backend1368 passed/8 skipped(390.79초). skip8개는 opt-in PostgreSQL이며 별도 실제 PostgreSQL8개를 모두 통과해 생략 근거를 분리했다. frontend209, UI250, production18, style-studio3 및 하네스·설정/브랜딩·discovery·패키징·계약 검사를 통과했다. 수동 범위 강등/receipt 수정/훅 우회는 하지 않았다.
- full 실행 중 추가 편집/중복 검사를 하지 않았다. 성공 후 결과용 worklog만 갱신하며 스테이징 governance/commit-msg·pre-push와 ready PR 실제 메타데이터 검증으로 이어간다. 병합은 root가 담당하며 이 기록은 아직 병합/배포를 주장하지 않는다.
- 원본 개발 DB에 수동 migrate/repair/stamp를 실행하지 않았다. root의 읽기 전용 점검에서는0030_board_media, 기존 baseline counts 동일(users1/나머지 기존 업무 테이블0), 새 board_media_assets/ref 각각0을 확인했다. 기존 개발 reload의 Alembic startup 적용으로 추정하며 스키마가 변경되지 않았다고 주장하지 않는다. env/시크릿/기존 파일은 보존했다.
- 기존 Canvas/프로필·다른 Board 보존, slot ready 복합 FK·일관 snapshot·권한/CAS/감사·실제 파일/worker/CLI와 실패/lease/위치/삭제 경쟁을 검증했다. 운영 제공자·처리량 SLA·제품 UI/크롭/썸네일·운영 배포는 이번 검증 범위가 아니다.
- source/계약/문서는 이 단일 feature 브랜치/커밋/ready PR에서 통합한다. #59의 마지막 merge/main 동기화·종료 항목과 부모 이슈의 UI/후속 범위는 root 인계 뒤 실제 근거로 갱신한다.
