# Commit Title

feat: 내 캔버스 목록과 휴지통 조회를 구현한다

# Changed File Scope

- 작성자 전용 목록 DTO/모델 저장소 canvas_list.py·기존 Canvas 라우터·서비스 DI·공유 순수 capabilities/기한 helper. 스키마/인덱스 변경은 없다.
- API/SQLite/실제 격리 PostgreSQL·인증 inventory 회귀, 한국어 문서·양쪽 계약·생성 타입.

# Reason

공개 목록과 공식 Board 홈은 main에 반영됐지만 본인 미게시 초안과 휴지통 목록은 없다. 상위 #8에서 백엔드 하위 이슈 #57을 분리해 기존 작성자 읽기·복구 정책과 일치하는 목록을 제공한다.

# Design

- GET /api/v1/me/canvases는 현재 활성 계정의 세션 사용자만 author 기준으로 조회한다. Board 운영 역할·전역 admin은 타인 초안 접근 권한이 아니다.
- status는 draft(기본)/trashed/all, publication은 all(기본)/published/unpublished의 별도 축이며 모든 선택 필터를 AND한다. sort는 last_modified 하나로 max(Canvas.updated_at, CanvasDocument.updated_at) 내림차순·Canvas UUID 내림차순이다. 게시/취소 자체는 편집 clock을 바꾸지 않는다. metadata/document의 기존 clocks와 revision은 변경하지 않는다.
- Board/Shelf scope는 active/archived Board의 현재 active 본인 멤버 기준이다. Shelf 읽기 등급은 본인 행 조회에 적용하지 않고 편집 capabilities에 적용한다. Shelf scope는 현재 read_canvas 허용 또는 status/publication/cursor와 독립적인 본인 Canvas 존재를 요구한다. 제한 Shelf에 본인 행이 없으면 존재를 노출하지 않도록404다. 없는/미허용/서로 다른 Board의 scope는 동일404, 허용 scope에 선택 필터와 맞는 본인 행이 없으면200 빈 목록이다.
- DTO는 CanvasResponse를 재사용한 항목에 document_updated_at/last_modified_at/trash_expires_at/trash_expired를 추가하고 목록 as_of를 한 번 캡처한다. 관계 이름/slug/정책은 노출하지 않는다. trash_expires_at=trashed_at+30일이고 as_of>=기한이면 만료한다. 만료 행은 조회되며 restore=false이다. 단건/목록은 같은 공개 capability helper를 사용한다.
- cursor는 canvas-owner-list/version1·현재 user_id·정규 status/publication/Board/Shelf hash·sort·UTC last_modified_at/UUID에 바인딩한다. limit은 바인딩하지 않아 페이지 크기 변경을 허용한다. canonical base64url·중복/추가 키·타입·2048 길이·명시 UTC를 검증한다. 현재 상태를 매 요청 재평가하며 페이지 간 편집/필터 전환은 고정 snapshot이 아니므로 새 첫 페이지가 필요하다.
- 단건 작성자 읽기와 같은 현재 Board/멤버 경계를 적용한다. 낮은 Shelf 등급의 자기 초안 읽기와 작성/복구·휴지통·공개본 취소 권한을 구분한다.
- limit/cursor는 현재 사용자·정규 필터/정렬·domain/version·UTC 시각/UUID에 묶는다. 허용 행을 먼저 판정한 뒤 page를 계산한다.
- models/canvas_list.py의 도메인 저장소가 PG REPEATABLE READ READ ONLY/SQLite BEGIN snapshot을 소유한다. 현재 계정/scope와 허용 author 행을 먼저 판정하고 limit+1 header를 조회한 뒤 관련 Board/member·grade·policy·현재 Tag를 고정 개수 batch로 읽는다. Shelf scope는 Board/member와 필터 독립 own-exists를1회 추가 읽고 동일 정책 batch에서 검사한다(비scope 최대6/Shelf scope 최대7 SELECT). 서비스는 기존 BoardPermissionService와 공유 capability helper로 계산한다. CanvasDocument/Publication JSONB 본문은 선택하지 않는다. 누락 Document는 단건과 같은503으로 처리하며 조용히 누락하지 않는다. SQL·세션·오류 변환은 모델에 유지하고 N+1·타 서비스 private 호출을 추가하지 않는다.
- 기존 DB/자료/환경을 보존하고 새 인덱스/migration은 필요 근거로만 최소 결정한다. startup은 Alembic만 사용한다.
- 신규 UI·독립 개인 Canvas·자동 purge/영구 삭제·미디어/사회적 기능은 후속이다.

# Verification Plan

- strict query/cursor·세션/auth inventory/API Key 거부·작성자/Board/제재/등급·단건 capabilities parity·페이지/같은 시각·복구 기한을 검증한다.
- SQLite/실제 고유 schema PostgreSQL로 관계/현재 상태/일관 읽기·본문 미로딩·기존 데이터 보존을 확인하고 schema를 정리한다.
- 양쪽 OpenAPI 값과 각 형식·생성 타입/TypeScript를 먼저 확인하고 VERIFY_BASE=951eac1c537e387d9a88690a80937ba9ce32b9f7 make verify-plan → make verify를 정상 범위/receipt로 수행한다.
- 정상 staged governance·commit-msg/pre-push·ready PR 실제 메타데이터/거버넌스와 merge commit/main 동기화 후 하위 이슈를 닫는다.

# Impact

기존 Board 소속 본인 Canvas의 목록과 휴지통 조회 계약을 추가한다. 기존 공개 목록과 작성/게시/복구 정책·데이터를 보존한다. 제품 UI/운영 배포는 포함하지 않는다.

# Loop Alignment

요청/현재 세션 → 서비스 DI·필터/cursor/현재 정책 → 모델의 일관된 본인 metadata/상태 조회 → 목록 DTO/다음 cursor 루프를 따른다. 프런트 런타임·실시간·worker·데스크톱 복구는 변경하지 않는다.

# Verification

- 사전 설계 뒤 root source QA의 제한/no-own Shelf 존재 노출 지적을 반영해 scope를 현재 read 허용 OR 필터 독립 own-exists로 보완했다. 첫 full/commit 전에 계획·이슈·문서·테스트를 갱신했다.
- targeted API/SQLite·기존 단건 초안/복구·게시·인증 inventory 회귀 135개가 통과했다. 초기 fixture import 누락 1건과 PG snapshot 테스트의 정렬 위치 가정은 테스트에서 수정했다.
- scope 보완 뒤 새 목록 SQLite 3개 + 실제 localhost PostgreSQL 1개를 다시 실행해 4개가 통과했다. PG는 고유 schema에 migration head 0029를 적용하고 현재 정책/페이지·정확한 기한·clock/counter/Tag/정책/제재 동시 변경의 RR snapshot·EXPLAIN·기존 인덱스·전체 테이블 읽기 전후 보존을 검사한 뒤 schema 삭제를 재확인했다. 기본 full의 opt-in skip과 이 별도 실행을 구분한다.
- global/Board 목록 6 SELECT, Shelf scope 7 SELECT를 실제 관측했다. limit 1/100 모두 항목 수와 무관한 고정 batch이고 Document/Publication 본문 JSONB 및 count를 SELECT하지 않는다. 응답 최대 100개와 lookahead 1개를 구분한다.
- make contract-export → 소비자 계약의 값 동기화/Prettier → frontend-api-generate 후 make contract-check frontend-api-check frontend-typecheck가 통과했다. provider JSON은 원래 indent 2를 유지했고 consumer JSON/TS만 Prettier를 적용했다. 소비자 2파일 Prettier check·변경 Python Ruff·git diff --check·backend-architecture-check도 통과했다.
- Router → DI service → 모델 DB 책임을 시작/완료 시 수동 검토했다. 서비스 DB 세션/SQL·타 서비스 private 호출·공개 피드/위젯 우회·원본 DB/env/파일/기존 startup 변경은 없다. 단건 API의 필드와 기존 정책/기한 경계를 유지한다.
- root의 최종 source/docs/contracts review 승인 후 VERIFY_BASE=951eac1c537e387d9a88690a80937ba9ce32b9f7 REDIS_IN_MEMORY=true make verify-plan → make verify를 정상 실행했다. 23파일 영향으로 backend 전체·frontend full 및 backend/branding/contracts/deployment/discovery/frontend-app/governance/harness/publication/style-studio 영역의 15명령을 선택했다. 수동 강등 없이 jobs=2에서 15명령을 실제 실행해 362.8초에 모두 통과했다. 로그: .git/verification-logs/run-2d4cs99i.
- full 실측 결과: backend 1,314 passed / 7 opt-in PostgreSQL skipped(355.77초), frontend unit 209 passed, UI 250 passed, production 18 passed, style studio 3 passed. 기본 full은 외부 PG opt-in을 실행하지 않으며 새 목록 PG 1개는 위 별도 실행에서 통과했다. 신규 UI/운영 배포는 요청 범위 밖이라 실행하지 않았다.
- full 성공 뒤 소스/테스트/문서/계약은 고정하고 이 결과 기록만 갱신했다. 정상 staged governance·commit-msg/pre-push 및 ready PR의 실제 거버넌스 결과는 해당 게시 근거로 확인한다. main 병합/이슈 종료는 root 인계 후 별도 확인한다.

# State Ownership

프런트 런타임 변경 없이 계약/생성 타입만 동기화한다.

# Memoization

프런트 런타임 변경이 없어 해당하지 않는다.

# Performance Evidence

한도·실제 SQL와 본문 미로딩/항목별 조회 부재를 확인하며 처리량 SLA를 주장하지 않는다.

# Page Family

## Family

신규 UI 변경 없음.

## Reference

기존 작성자 단건/초안·휴지통/복구와 공개 목록 계약.

## Shared Rules

한국어·단일 저장소·DI·모델 DB 책임·계약 동기화.

## Exceptions

없음. 위 필터/정렬/기한 계약은 구현 전 확정했다. 인덱스는 기존 author/Board/Shelf 인덱스와 실제 PG plan을 먼저 확인하며 SLA를 주장하지 않는다.

## Evidence

새 화면 비교는 해당하지 않는다. 루트가 선택한 기존 회귀는 유지한다.
