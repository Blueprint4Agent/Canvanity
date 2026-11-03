# Commit Title

feat: 자유 태그 사전과 캔버스 태그 연결을 구현한다

# Changed File Scope

- Tag 도메인의 모델/저장소·라우터·서비스·오류와 migration, Canvas 생성/metadata 태그 연결.
- API/정규화/SQLite/실제 격리 PostgreSQL 회귀와 기존 공통 인증 목록.
- 양쪽 OpenAPI와 프런트 생성 타입, 한국어 Tag/설계 문서·가이드와 이슈 #49 진행 기록(#24는 부모 이슈로 참조).

# Reason

main bca11d5에 실제 본문 저장을 반영했다. 공식 Interest와 별도 자유 Tag를 검색/생성하고 작성자에게 허용된 Canvas의 metadata에 연결해야 한다. UI를 포함한 상위 #24와 별개로 #49를 백엔드 완료/병합/종료 단위로 추적한다.

# Design

- 기존 NFC/trim/casefold·표시명40/정규화80·Canvas당10 기준을 구현하고 입력 거부/정렬/중복 재사용·응답 정책을 계약으로 명확히 한다. 최초 표시명과 같은 정규화 키의 Tag 식별자를 보존한다.
- 공개 Tag 사전은 최소 ID/이름만 반환하고 비공개 Canvas 연결/사용 건수는 노출하지 않는다. 공식 Interest와 Board 자유 Tag는 변경하지 않는다.
- 세션 전용 생성과 현재 Canvas 작성자/계정·멤버/Board/Shelf 권한·metadata revision을 재사용한다. 태그와 다른 metadata는 한 트랜잭션에서 변경하고 document revision/본문·Asset refs를 보존한다.
- SQL/세션/트랜잭션/ORM 쓰기·고유 제약/driver 오류 변환은 models/tag.py와 models/canvas.py 안에 둔다. 별도 Repository 파일이나 서비스 DB 호출은 추가하지 않는다.
- 실제 migration head 뒤의 새 migration은 필요한 Tag 테이블만 생성하며 기존 Canvas/본문/에셋/참조/outbox를 보존한다. 구체적 endpoint/필드/상태·원자적 no-op 정책은 구현 전 현재 패턴을 확인한 뒤 추가 기록한다.

구현 전 확정한 세부 계약:

- 표시명은 valid UTF-8이며 제어(Cc)·포맷(Cf)·서로게이트(Cs) 문자를 원본 단계에서 거부한다. NFC 후 Unicode 앞뒤 공백을 제거한 1~40자다. 정규화 키는 표시명을 casefold한 뒤 다시 NFC로 만든 1~80자다. 호환 정규화/기호 제거는 하지 않으므로 한글·C++·C#을 보존한다.
- GET /tags는 공개이며 q는 같은 정규화 규칙의 0~40자(빈 값은 전체), limit는 기본20/최대50이다. 정규화 키의 literal 부분일치를 사용하고 키의 binary 순서/UUID로 정렬한다. 응답은 items의 id/name뿐이다. POST /tags는 현재 active 계정의 세션만 허용하고 최초 생성201/동일 키 재사용200에 같은 id/name DTO를 반환한다. 단건 GET·Location·개수/작성자/Canvas 연결은 제공하지 않는다.
- CanvasCreateForm.tag_ids는 기본 빈 배열, PATCH는 생략 시 유지/빈 배열 시 해제다. 최대10·중복 UUID·없는 UUID·null·서버 소유 추가 필드를 거부한다. CanvasMetadata.tags는 id/name 요약을 검색과 같은 순서로 반환한다.
- metadata PATCH는 현재 권한/expected_revision을 먼저 검사하고 태그/일반 필드를 한 트랜잭션에서 바꿔 실제 변경이 있을 때만 revision을 한 번 올린다. 동일 집합(입력 순서만 다름)은 no-op이며 잘못된 expected_revision은 no-op에서도409다. 생성/수정 모두 Tag 연결 실패 시 전체 rollback한다.
- 기존 API 설계의 사용자별 생성/검색 rate limit은 구현 전 제안이며 익명 공개 검색과 맞지 않아 이번 범위의 구현된 계약에서 제외한다. 검색 결과/입력 크기를 제한하며 분산 rate limit·추천·Tag UI·Board Tag는 후속이다.

# Verification Plan

- 한글·C++/C#·Unicode 정규화/길이/중복·동시 재사용, DTO/검색·인증/API Key 거부를 검증한다.
- SQLite/실제 PostgreSQL 고유 schema에서 Tag 고유성/FK·metadata 경쟁/권한 회수/rollback과 기존 본문/Asset 참조 보존을 확인한다.
- source/한국어 문서/계약을 마친 뒤 기준 bca11d51f3dc055b48b1aa15b484dba88a643d77의 루트 make verify-plan → make verify를 따른다. 새 endpoint 공통 인증 inventory를 먼저 대조한다.
- 정상 commit-msg/pre-push·실제 PR Type/라벨/ready/base/head/이슈 연결·거버넌스를 확인하고 병합/종료는 근거로 구분한다.

# Impact

Tag 사전과 Canvas metadata에 기능을 추가한다. 기존 Interest·Board/Shelf·문서 PUT/CAS·이미지 저장과 공개/초안 비밀 경계를 유지한다. 신규 UI·추천·Board Tag·publish/공개 snapshot은 후속이다.

# Loop Alignment

요청/세션 또는 공개 조회 → 서비스 DI/현재 정책 → 모델 정규화/SQL·metadata CAS → 최소 Tag/Canvas 응답 → 계약/생성 타입 루프다. 태그는 서버 metadata이고 문서 편집/실시간·worker/데스크톱 복구·UI 상태는 변경하지 않는다.

# Verification

- 작업 시작: feat/canvas-tags / main bca11d51f3dc055b48b1aa15b484dba88a643d77. 부모 세션이 만든 미추적 계획 worklog만 있음을 확인한 뒤 위 세부 계약을 구현 전에 확정했다.
- 대상 검사: 정규화·Tag/Canvas HTTP 계약·실제 API Key 거부 공통 목록 143개 통과(17.64s), SQLite 통합 9개 통과(6.93s), backend architecture 통과(135 Python files/fixture4).
- 실제 PostgreSQL 최초 검사: 임시 고유 schema에서0027 기존 Canvas/본문/Asset/ref/outbox 데이터 생성→0028 upgrade 보존·정규화 중복 생성 경쟁·metadata CAS·권한 회수 lock wait·FK/commit rollback·두 Board 재사용·schema 제거까지1개 종합 시나리오 통과(1.09s).
- 요구 경계 보강 후 SQLite9+실제PG1 통합10개 통과(6.86s). 최대10개 정상 생성과 Tag 생성이 User 공유 잠금을 기다린 뒤 비활성 계정을 거부하는 실제 경쟁까지 추가 확인했다. 선행 성공 검사는 이 추가 검증의 변경 이유와 구분한다.
- 루트 OpenAPI export→frontend snapshot 명시 복사→생성 타입 갱신을 수행했다. 현재 UI/runtime 소스는 변경하지 않았다.
- 기준 SHA를 지정한 make verify-plan은 backend 전체·frontend full과 전체15명령을 선택했다. 모델/migration·기존 계약/생성 타입·가이드의 공유 영향 때문에 축소하지 않았다. 같은 기준의 make verify가15명령/jobs2·305.9s에 모두 통과했다. 로그: .git/verification-logs/run-byz523_u.
- 전체 결과: backend1090 passed/3 skipped·300.24s, frontend209, UI250, production18, style-studio3 통과. 스킵3개는 실제 PostgreSQL opt-in 검사이며 이번 태그 PG는 위 별도 실행에서 통과했다. root/frontend 하네스·정적/아키텍처·계약/생성 타입·브랜딩·가짜 Docker/패키징도 통과했다. 기존 Pydantic/argon2/프로필 deprecated 경고는 이 범위에서 수정하지 않았다.
- 완료 수동 검토: 요청→TagService/CanvasService→모델·공유 가드의 DI 경로, main 라우터 등록, 도메인 오류/HTTP 상수, SQL/세션/ORM 쓰기의 모델 소유권, 서비스 간 private 호출 없음과 metadata 입력/ORM 필드 분리를 확인했다. 자동 architecture 통과가 이 전체 경계를 보장한다는 주장은 하지 않는다.
- 생략: 신규 UI/제품 편집기·실시간/worker 변경과 운영 배포는 요청 범위 밖이다. 새 화면 비교는 해당하지 않지만 계획이 선택한 기존 전체 브라우저/프로덕션 회귀는 실행했다. 성능 부하 시험은 실행하지 않았으며 부분일치 검색의 결과 limit를 scan 비용 한도로 설명하지 않는다.
- 전체 성공 이후 소스/계약/개발 문서는 변경하지 않았다. 정상 commit-msg/pre-push와 ready PR/실제 메타데이터 검증으로 이어가며 게시·main 병합·이슈 종료의 최종 근거는 #49/해당 PR에서 구분한다.

# State Ownership

프런트 런타임 없이 생성 타입만 동기화한다.

# Memoization

프런트 런타임 변경이 없어 해당하지 않는다.

# Performance Evidence

검색/이름/개수 제한과 실제 검증을 기록하며 성능 SLA를 주장하지 않는다.

# Page Family

## Family

화면 변경 없음.

## Reference

기존 공식 Interest와 Canvas metadata/API 패턴.

## Shared Rules

한국어·단일 저장소·DI·모델의 관계형 세션 소유권과 계약 동기화.

## Exceptions

없음.

## Evidence

신규 UI가 없어 화면 비교는 해당하지 않는다. 선택한 기존 브라우저 회귀는 유지한다.
