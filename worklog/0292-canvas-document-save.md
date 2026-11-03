# Commit Title

feat: 캔버스 본문을 버전 충돌과 이미지 참조를 검증해 저장한다

# Changed File Scope

- Canvas 라우터/서비스·공유 접근 가드·모델의 PUT 문서 저장 계약과 SQL CAS.
- 모델/저장소 안에서 Asset draft 참조를 조합하고 현재 ready/동일 Canvas 경계를 검증한다.
- API·SQLite/실제 격리 PostgreSQL·공통 세션 인증 회귀, 양쪽 OpenAPI와 프런트 생성 타입.
- 한국어 저장/객체/에셋·설계 문서·가이드와 이슈 #47 진행 기록. 상위 #7 갱신과 병합/종료는 부모 세션이 맡는다.

# Reason

PR #46으로 실제 객체 스키마를 main 224cc9b에 반영했다. 다음은 편집 데이터를 저장하고 기대 문서 revision 경쟁의 덮어쓰기와 본문/이미지 참조 불일치를 막는 백엔드 수직 구현이다. #7 전체에는 UI/복구가 남아 있으므로 #47을 별도 완료/병합/종료 단위로 추적한다.

# Design

- 세션 전용 PUT은 엄격한 expected_revision/document를 받고 문서 저장 revision을 반환한다. 메타데이터 revision은 바꾸지 않는다.
- 라우터의 전송 어댑터에서 JSON 디코딩 전 실제 수신 바이트를 제한하고 선언 Content-Length만 신뢰하지 않는다. 객체/정규화 UTF-8 문서 검증은 기존 CanvasContent를 재사용한다.
- CanvasService는 DI로 현재 작성자·계정/멤버·Board/Shelf 액션 권한·draft 상태를 검사한다. SQL/잠금/CAS·ORM 쓰기·commit/rollback·드라이버 오류 변환은 models/canvas.py·models/asset.py 안에 둔다.
- Board→User→Canvas→Document→정렬한 Asset→Outbox 잠금과 하나의 DB 트랜잭션에서 문서/revision과 draft 참조를 갱신한다. 기존 publication 참조는 보존한다. 외부 파일 I/O는 추가하지 않는다.
- body가 같은 저장도 현재 revision을 조건으로 새 문서 revision을 부여한다. 오래된 기대 버전/상한은 문서 전용 409/current_revision이다. invalid asset은 기존 도메인 계약 또는 명시적 Canvas 도메인 예외로 일관되게 반환한다.
- Asset replace_refs의 기존 ready 상태/미사용 TTL·정리 claim 직렬화를 재사용하고 다른 Board/Canvas 행을 잠그지 않게 조회를 한정한다.
- 구현 중 루트 아키텍처 검사가 라우터의 모델 상수 import를 거부했다. 검사 기준은 유지하고 공용 JSON/전송 바이트 한도를 순수 기술 모듈 utils/canvas_limits.py로 옮겼다. FastAPI 입력 검증과 Asset 도메인 오류의 서로 다른 422 envelope도 명시적인 스키마 대안으로 보존했다.

# Verification Plan

- 입력/인증/413·422/409·capabilities와 저장→GET을 API/실제 SQLite로 검증한다.
- 두 연결/실제 PostgreSQL 고유 schema에서 단일 CAS 승자, 한글 JSONB·Asset 참조·rollback·권한 회수/cleanup 경쟁을 검증한다. 기존 데이터/시크릿과 다른 Board/프로필 파일을 보존한다.
- 기준 224cc9bb13b1a652c2a0dbff9e8f80019beda3a9의 루트 make verify-plan → make verify가 선택한 범위를 따른다. 성공한 동일 입력은 정상 receipt 정책으로 재사용한다.
- 문서/계약을 마친 후 최종 검증, 정확한 worklog 제목과 정상 commit-msg/pre-push·실제 PR Type/라벨/ready/base/head/연결·병합을 확인한다.

# Impact

새 PUT과 문서 편집 capabilities·도메인 오류를 추가하고 기존 GET/메타데이터/에셋·파일 수명주기를 보존한다. 제품 편집기·자동 저장/복구 UI·게시 snapshot·배포는 후속이다. DB 구조를 바꿀 필요가 없는 한 migration을 추가하지 않는다.

# Loop Alignment

요청 전송 상한 → 인증/DTO → CanvasService/공유 가드 → 모델의 CAS/동일 트랜잭션 참조 → revision 응답/GET 복원과 계약/생성 타입 루프다. 기존 에셋 cleanup outbox/worker와 보호 참조를 연결하되 새 작업 종류/파일 I/O를 만들지 않는다. UI/실시간/데스크톱 복구 루프는 변경하지 않는다.

# Verification

- 시작 상태: main 224cc9bb13b1a652c2a0dbff9e8f80019beda3a9 기준 feat/canvas-document-save. 부모가 구현 전 계획 worklog만 만든 상태를 새 컨텍스트에서 인계했고 다른 기존 변경은 없었다. 이후 소스/문서/Git 변경은 이 세션이 맡았다.
- 집중 API 검사 70 passed, 기본 opt-in PostgreSQL 1 skipped(1.36s). 실제 SQLite 본문/기존 초안 회귀 49 passed(33.64s). 비활성 계정의 새 테스트 기대값 401을 기존 인증의 USER_NOT_FOUND 404에 맞췄으며 제품 인증은 바꾸지 않았다.
- 최종 런타임 소스 기준 실제 로컬 PostgreSQL 검사 1 passed(1.35s). 고유 canvanity_document_test_<uuid> schema의 실제 migration/JSONB·2연결 CAS·FK/flush/commit rollback·Board 잠금 대기 중 등급 회수·저장 선점/cleanup claim 선점 두 순서를 확인했다. 임시 ObjectStorage와 schema를 정리하고 schema 부재를 재조회했다. 기존 사용자 DB/Board/프로필 파일은 보존했다.
- 전체 검증 첫 실행은 모델 상수의 라우터 import 때문에 architecture-check에서 실패했다. 공용 기술 상수로 정리한 뒤 architecture-check와 기존 fixture 4개가 통과했다. 검사기를 완화하지 않았다.
- 두 번째 전체 검증에서 공통 인증의 명시적 session-only inventory가 새 PUT을 빠뜨린 1건을 발견했다(백엔드 1034 passed/1 failed/2 skipped, 289.36s). 실제 발급 API Key 거부 루프와 정확한 목록에 PUT만 추가했다. 다른 Canvas endpoint 목록도 공통 auth/test/scripts에서 대조했다. 공통 인증 2개 + 새 API 전체는 72 passed(2.41s)로 확인했다.
- 최종 VERIFY_BASE=224cc9bb13b1a652c2a0dbff9e8f80019beda3a9 REDIS_IN_MEMORY=true make verify-plan → make verify는 모델/계약의 공유 영향으로 전체 15명령을 선택해 237.3s에 통과했다. 백엔드 1035 passed/2 skipped(실제 PostgreSQL opt-in), 231.96s다. 프런트 209개·전체 UI 250개·프로덕션 18개·스타일 3개는 내용이 같은 성공 receipt를 정상 재사용했다. 하네스·초기화·아키텍처·env·Ruff·계약·브랜딩/빌드/패키징도 선택 계획대로 통과했다. 소스 변경으로 receipt가 무효화된 검사만 재실행했고 수동 생략/강등하지 않았다. 최종 로그는 .git/verification-logs/run-84u9proc다.
- make contract-export → 루트 계약의 프런트 기준 파일 명시 복사 → make frontend-api-generate와 프런트 JSON Prettier를 수행했다. source.json은 이미 same-commit 단일 저장소 출처여서 변경하지 않았다. 새 Markdown 링크 41개와 git diff --check를 확인했다.
- 수동 책임 경계 검토: 라우터는 순수 바이트 전송/DTO/응답만, 서비스는 생성자 DI와 현재 정책/상태 판단만 수행한다. SQL·행 잠금·CAS·ORM 필드·flush/commit·드라이버 오류 변환과 같은 세션의 ref 조합은 기존 두 모델에 유지한다. 다른 서비스 private 호출·새 서비스 전달 계층·DB 잠금 안 파일 I/O는 추가하지 않았다. 허용된 순수 전송 어댑터를 관계형 경계 위반으로 취급하지 않았다.
- 새 UI/편집기·오프라인/실시간 복구·게시 snapshot·Tag·운영 배포는 요청 범위 밖이므로 구현하지 않았다. 새 migration은 기존 0026/0027 구조를 재사용하여 불필요하다. 실제 PG 검사는 opt-in이라 기본 전체 테스트의 skip과 구분한다.
- 최종 소스 이후에는 이 결과 기록만 수정한다. 정확한 제목/본문·staged worklog와 정상 commit-msg/pre-push를 유지해 커밋/푸시/ready PR을 게시한다. 실제 원격 SHA·라벨·base/head·draft와 PR 거버넌스 결과는 #47/PR에서 기록하며 병합/종료는 부모 세션이 담당한다.

# State Ownership

프런트 런타임을 변경하지 않고 생성 타입만 동기화한다.

# Memoization

프런트 런타임 변경이 없어 해당하지 않는다.

# Performance Evidence

원시 요청 2,162,688바이트의 정확한 허용 경계와 초과/거짓 Content-Length·chunked 거부, 정규화 문서 2 MiB의 별도 422를 확인했다. PostgreSQL 실측 1.35s는 이 로컬 시나리오 1회이며 API/저장 SLA로 설명하지 않는다.

# Page Family

## Family

화면 변경 없음.

## Reference

기존 Canvas/Board/Asset와 공용 계약을 따른다.

## Shared Rules

한국어·단일 저장소·DI·모델의 관계형 세션 소유권을 유지한다.

## Exceptions

없음.

## Evidence

UI 변경이 없어 신규 화면 비교는 해당하지 않는다. 선택한 기존 브라우저 검사는 유지한다.
