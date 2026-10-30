# Commit Title

feat: 캔버스 이미지 에셋과 파일 정리 outbox를 구현한다

# Changed File Scope

Canvas 이미지 업로드/조회/삭제 API·공유 작성자 가드·에셋 모델/저장소와 migration, 원래 저장 위치 식별·기존 오브젝트 스토리지 연동, Board 삭제 outbox·정리 서비스/Beat·운영 재처리 CLI, API/통합/실제 PostgreSQL 회귀, 양쪽 OpenAPI·생성 타입과 한국어 문서. #6, #8/#22/#1 연계. UI·운영 배포는 제외한다.

# Reason

Canvas 본문에 바이너리 대신 에셋 ID를 연결할 실제 저장 기반이 필요하다. 파일 I/O와 DB 실패·취소/중단·Board 삭제가 고아 파일이나 잘못된 공유 파일 삭제를 만들지 않도록 추적 가능한 업로드 의도와 삭제 재시도를 구성한다.

# Design

기준 7631143dd4945a46de2e82b40d147c37589be137, feat/canvas-assets. 선행 초안 PR #42가 main 미병합이므로 feat/canvas-draft-foundation 기준으로 분리한다. 기존 ObjectStorage DI를 사용하고 SQL/세션·잠금/트랜잭션·ORM 쓰기·드라이버 오류 변환은 models/asset.py에 둔다. Canvas와 에셋은 공유 CanvasAccessService의 현재 작성자·멤버/등급/상태 가드를 사용한다. 파일 I/O는 DB 잠금 밖에서 실행한다. pending 에셋과 정리 outbox를 put 전에 원자 예약하고 성공 시 ready 전환/미참조 TTL을 기록한다. outbox는 Board FK 없이 키·저장 위치 지문/비밀 없는 원래 위치를 보존하고, 삭제 직전 참조·위치를 재검사하며 fencing lease·최대 시도·운영 재처리를 지원한다. Board→User→Canvas→Asset→outbox 순서를 유지하고 ready 참조 FK로 삭제 중인 파일의 재연결을 막는다.

# Verification Plan

실제 이미지/위장·손상·입출력 8 MiB·총 16MP/최대 100프레임·메타데이터 제거, 업로드/재조회·쓰기 권한 회수·초안 비밀·상위 상태·실제 API Key, 파일/DB 실패·취소·업로드 완료 경쟁·늦은 완료·보관 삭제·공유/프로필 참조 보존을 검증한다. outbox의 중복 실행/만료 lease·fencing·실패 backoff/최대 시도·저장 위치 불일치·CLI 재처리를 확인한다. SQLite의 기존 Canvas/문서 보존 migration 왕복과 실제 PostgreSQL 제약/참조·워커/삭제/업로드 경쟁을 확인한다. 루트 VERIFY_BASE=7631143 make verify-plan → VERIFY_JOBS=1 VERIFY_BASE=7631143 make verify를 실행한다.

# Impact

본문 저장/실제 에디터 이미지 붙여넣기·드롭·publication 연결은 #7/#8과 UI 후속이다. 현재 이미지 형식은 PNG/JPEG/WebP/GIF 실제 내용을 검증한 뒤 제한된 WebP로 정규화한다. pending 업로드 1시간·미참조 ready 24시간의 정리 대상 시각을 사용하며 물리 삭제 시각 보장으로 설명하지 않는다. 현재 저장소와 지문이 다르면 삭제하지 않고 운영자가 원래 설정에서 재처리한다. 프로필 사진의 기존 실패 보상 동작을 보존하고 새 outbox 보장으로 확대하지 않는다. 운영 스토리지 구매/연결·실배포는 하지 않는다.

# Loop Alignment

요청→라우터→DI 에셋 서비스/공유 Canvas 가드→모델 저장소→ObjectStorage→현재 상태 재검사/저장→응답이다. 삭제는 원자 outbox→주기적 Beat/워커→참조/위치 재검사→파일 삭제→fenced 완료/재시도로 복구한다. UI/프런트 런타임·실시간·데스크톱 루프는 이번 범위 밖이다.

# Verification

시작 트리는 깨끗했고 PR #42 open/draft·head 7631143·main 미병합을 확인했다. 기존 stash는 적용하지 않았다. 구현 전 ObjectStorage/프로필 보상과 모델 책임 경계를 읽고 PostgreSQL 잠금/짧은 트랜잭션 기준을 적용했다.

대상 API·이미지·파일 저장/프로필 회귀의 최초 90개 중 88개가 통과했고 잘못된 테스트 입력 2개를 수정했다. 탈퇴는 존재하지 않는 left enum을 쓰지 않고 멤버 행을 제거하며, Board DELETE는 지원하지 않는 reason을 보내지 않는다. 수정 후 SQLite 통합 21개와 migration 보존/거부를 통과했고, 독립 CLI 테스트의 DB 설정 입력도 기존 DB_DRIVER/DB_NAME 구성에 맞췄다. 독립 CLI 1개(2.30초)가 같은 격리 DB/local 저장소에서 파일을 정리했다. DebugMCP 응답이 없어 live debug 세션은 확인하지 못했고 실패 기록과 설정 구성 코드를 대조했다. 운영 설정/데이터를 변경하지 않았다.

실제 localhost PostgreSQL의 고유 schema 검증 1개(2.83초) 통과: 전체 migration 왕복, JSONB·ready 상태/동일 Canvas 복합 FK, 참조/정리 경쟁과 중복 worker 단일 claim, 만료 lease·stale token 거부, 파일 put 중 Board 보관/영구 삭제·부모 없는 outbox와 늦은 완료 후 정리를 확인했다. 테스트 뒤 schema를 삭제하고 부재를 확인했다. 추가 프로필/타 Canvas·draft/publication 참조·파일 위변조/원래 위치·quota, 파일 실패/취소·예약/후속 DB 실패와 실제 commit 뒤 오류의 ready 보존·재시도/backoff/최대 시도·late put 재처리를 검증했다.

루트 VERIFY_BASE=7631143 make verify-plan → VERIFY_JOBS=1 VERIFY_BASE=7631143 make verify의 15개 명령 전체 통과(663.5초). 백엔드 899 통과·PostgreSQL opt-in 1 skip(별도 실제 실행 통과), 프런트 단위 207·브라우저 250·production 18·style-studio 3 통과. 아키텍처·Ruff/타입·양쪽 OpenAPI/생성 타입·설정/도구·프로젝트 빌드/패키징을 통과했다. 추가 변경 없는 성공 검증을 반복하지 않고 유효한 로컬 receipt는 필수 훅에서 재사용한다.

시작/완료 수동 책임 검토: 라우터는 전송·파일 스트림/응답만, DI 서비스/공유 가드는 현재 역할/등급/상태와 업무 흐름만 소유한다. SQL·세션·트랜잭션·ORM 쓰기·드라이버 오류 변환은 models/asset.py 및 기존 모델에 있고 별도 Repository 파일/타 서비스 private 호출은 없다. AssetCleanupService의 dispose_db는 독립 worker 종료 시 인프라 자원 해제이며 관계형 업무 CRUD가 아니다. 오류 enum/HTTP 상수·영어 기본 메시지를 유지한다. UI·프런트 런타임 변경이 없어 화면/상태/memo/성능 실험은 추가하지 않는다. 문서 저장/공개본 연결·운영 배포는 실행하지 않았다. #6 전체는 열린 상태로 유지한다.
