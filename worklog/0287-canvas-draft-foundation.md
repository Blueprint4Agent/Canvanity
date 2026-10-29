# Commit Title

feat: 캔버스 초안과 Shelf 소속 및 수명주기 기반을 구현한다

# Changed File Scope

Canvas 모델/저장소·DI 서비스·라우터/도메인 오류와 migration, 기존 Board/Shelf 삭제 경계·공유 권한 평가기, API/통합/실제 PostgreSQL 회귀, 양쪽 OpenAPI·생성 타입과 한국어 문서. #8의 최소 기반, #23/#22/#1 연계. 제품 UI·운영 배포는 제외한다.

# Reason

사용자가 허용된 Shelf에 초안을 생성하고 자신의 메타데이터/빈 문서를 읽으며 같은 Board 안에서 분류를 바꿀 수 있어야 한다. 초안 비밀 경계와 현재 등급·역할·제재를 지키고 새 게시글 참조가 있는 Shelf/Board의 기존 삭제가 데이터를 잘못 정리하지 않도록 연결한다.

# Design

기준 688bbf85346db28ce73e71308134ed9f9b49ff09, feat/canvas-draft-foundation. 선행 초안 PR #41이 main 미병합이므로 feat/shelf-management 기준으로 분리한다. canvases·canvas_documents와 JSONB 빈 본문을 같은 트랜잭션으로 생성한다. 같은 Board/Shelf 복합 FK·RESTRICT와 author_id SET NULL을 적용한다. 메타데이터 revision과 본문 revision은 분리한다. 작성자 전용 조회·허용 메타데이터 PATCH·휴지통/30일 내 복구를 제공한다. SQL·세션·ORM 쓰기·잠금/commit·오류 변환은 models/canvas.py의 저장소가 소유하고 같은 세션의 BoardTransaction 공개 연산을 조합한다. Board→활성 계정→Canvas→Document 순서로 잠그고 생성·편집/이동·복구는 현재 읽기/작성 정책, 자신의 초안 조회/휴지통은 낮은 등급에서도 활성 멤버에게 허용한다. Board 보관 삭제에 현재 Canvas/문서를 포함하고 active 빈 Board·Shelf 비어 있지 않음 검사에 초안/휴지통을 모두 포함한다.

# Verification Plan

입력·인증/실제 API Key·작성자 비밀 경계·운영 역할/등급 분리·숨김/공지/비공개/보관/정지·제재, 생성/문서 원자성·내용/소속/불변 필드·같은 Board 이동·현재 정책/강등·metadata/document revision·no-op/stale/rollback·휴지통/복구 만료를 검증한다. 실제 PostgreSQL의 JSONB·복합 FK/RESTRICT·SET NULL·동시 변경 단일 승자·삭제/이동 경쟁과 migration 왕복을 확인한다. 루트 VERIFY_BASE=688bbf8 make verify-plan → VERIFY_JOBS=1 VERIFY_BASE=688bbf8 make verify를 실행한다.

# Impact

현재 draft/trashed와 빈 본문만 지원한다. 문서 편집/저장·publish/publication/공개 목록·Tag/에셋·자동 purge/외부 작업은 #7/#8/#24/#6의 후속이다. 공개 상태를 생성하거나 임시 공개 목록을 가장하지 않는다. 현재 파일 참조가 없어 outbox/worker는 추가하지 않는다. 계정 삭제 시 문서 author_id는 기존 설계대로 null로 남고 다른 사람에게 초안 접근을 부여하지 않는다. #8 전체와 main 병합은 별도로 추적한다.

# Loop Alignment

요청→라우터→DI CanvasService/공유 Board 가드→모델 저장소/잠금 트랜잭션→DTO 응답이다. Board/Shelf 서비스는 해당 aggregate의 저장소 공개 연산만 사용하고 Canvas 서비스 private 메서드를 호출하지 않는다. 프런트 런타임·실시간/worker·데스크톱/UI 루프는 이번 범위에 해당하지 않는다.

# Verification

구현 전 계획. 시작 트리는 깨끗하다. PR #41 open/draft·head 688bbf8·main 미병합을 원격에서 확인했다. 기존 SQL/세션은 모델이 소유하며 사용자의 기존 stash는 적용하지 않는다. 실제 결과·생략 이유와 완료 경계 검토는 이후 기록한다.

- 대상 API·통합·인증: 98 passed, 4 warnings, 31.99초. 작성자/운영 역할·같은 토큰의 강등/제재·자기 초안 읽기/휴지통 예외·보관/정지·공지/숨김·소속 이동·메타데이터/문서 독립 revision·no-op/stale·30일 경계와 초기 문서/메타데이터 rollback을 확인했다.
- 실제 PostgreSQL: 1 passed, 2 warnings, 1.76초. board/canvas/user 저장소 모두 격리 schema에 연결했다. JSONB·BIGINT·복합 FK/RESTRICT·author SET NULL과 migration 왕복, 메타데이터 경쟁 단일 승자/409·권한 회수 후 편집 거부·생성/삭제와 계정 삭제 경쟁, 이동/생성/휴지통 commit 실패의 원자성을 검증했다. 기존 Board 종료 검사가 새 Canvas/문서를 모두 정리하는 것도 확인했다.
- 다른 Board 문서 보존을 확장한 보관 삭제 검사: 1 passed, 3 warnings, 0.89초. 단독 Owner의 active Board도 초안/휴지통이 있으면 삭제를 거부하고, archived 확인 삭제는 실패 시 문서까지 롤백하며 성공 시 해당 Board 자료만 정리한다.
- VERIFY_BASE=688bbf8 make verify-plan → VERIFY_JOBS=1 VERIFY_BASE=688bbf8 make verify: 공유 모델·신규 migration/인증 계약으로 전체 15명령 선택/통과, 488.3초. 백엔드 859 passed / 실제 PG opt-in 1 skipped / 37 warnings(별도 실제 PG 통과), 프런트 단위 207·브라우저 250·production 18·style-studio 3 통과. 아키텍처·Ruff·프런트 타입/포맷·양쪽 OpenAPI/생성 타입·설정/도구·빌드/패키징 통과. 로그: .git/verification-logs/run-zu4t7w29.
- 기존 OpenAPI 의미 비교: 기존 경로/연산 정의는 같고 ShelfErrorDetail에 비어 있지 않음 오류를 추가했다. 신규 4경로의 6연산과 12개 스키마를 추가했다. 제공자/소비자 계약과 생성 타입을 같은 변경에서 갱신하고 same-commit 출처를 유지했다.
- 완료 수동 경계 검토: main의 신규 등록과 라우터는 전송/서비스 호출, CanvasService는 현재 작성자·상태·공유 Board 권한과 저장소 공개 연산을 사용한다. SQL/세션/ORM 쓰기·잠금/commit·드라이버 오류 변환은 models에 있고 서비스 간 private 호출은 없다. 도메인 Exception/ErrorCode·HTTP 상수·영어 기본 메시지를 사용한다. Board/Shelf 삭제도 저장소 연산으로만 확장했으며 별도 Repository 파일·자동 경계 검사기는 추가하지 않았다.
- 새 UI·프런트 런타임/상태·실시간/worker·자동 purge·배포는 범위 밖이다. 기존 검토 어댑터의 빈 문서 포맷만 준비했고 제품 편집기 채택/설치를 완료했다고 설명하지 않는다. #6의 실제 에셋/삭제 outbox → #7 문서 저장/요소 검증 → #8 공개본/목록과 #24 Tag를 후속으로 유지한다. #8 전체 완료와 main 병합은 별도다.
