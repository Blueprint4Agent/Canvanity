# Commit Title

feat: 캔버스 객체 스키마와 문서 검증 모델을 정의한다

# Changed File Scope

- `src/backend/app/models/canvas.py`: 문서와 객체 타입·구조 검증. 관계형 저장소 경계는 유지한다.
- Canvas 문서 검증 회귀·실제 고정 버전 엔진 export fixture, 양쪽 OpenAPI와 프런트 생성 타입.
- 전체 검증 중 실패를 재현한 기존 `admin-demo.spec.ts`의 배치 비교 대기와 `minimal-workspace.spec.ts`의 DOMRect 소수점 높이 비교를 보완하고 프런트 테스트 가이드에 기록한다. 제품 화면/상태/스타일은 바꾸지 않는다.
- `notes/community/`의 객체 스키마 계약·기존 설계/초안 문서·진입 링크, 백엔드 가이드.
- `board-api-status.md`와 이슈 #22에서 현재 main의 Board API 완료/미완료 범위를 대조한다. 기존 설계의 독립 GET membership은 현재 없으며 상세/홈 응답의 본인 membership과 구분한다.
- 이슈 #5의 스키마 정의와 #7의 선행 타입/검증 진행 기록.

# Reason

현재 본문은 빈 nodes/edges를 담는 list[dict] 틀만 있다. 실제 객체 스키마 확정과 구현이 저장 API에 앞서 추적되도록 텍스트·이미지·그림·도형·연결선의 필드와 버전·참조·제한을 문서/타입/회귀로 구체화한다. 설계 완료와 저장/편집기 구현 완료를 구분한다.

# Design

- 기존 schema_version=1, 고정 엔진/어댑터와 빈 문서의 기본 JSON을 유지한다.
- 타입별 허용 필드와 유한 좌표/크기·ID·연결 참조·전체 순서·텍스트/포인트·UTF-8 크기 제한을 검증한다. 엔진 필드의 임의 JSON 통과와 URL/바이너리 영속화를 허용하지 않는다.
- 문서 내부 구조 검증은 모델이 소유한다. 실제 asset 존재/소속/ready·현재 권한·SQL 잠금/CAS·draft 참조 갱신은 #7 저장 API의 후속 책임이다.
- 현재 GET의 문서 응답 계약과 양쪽 snapshot/생성 타입을 함께 구체화한다. 새 PUT/publish·UI·migration은 이번 범위에 포함하지 않는다.
- 바깥 JSON은 snake_case이고 engine_element만 고정 엔진 필드명을 보존한다. 실제 독립 화면의 5요소 export를 fixture로 고정하고 임시 파일 ID를 논리 Asset UUID로 바꾼다. 제품 편집기 채택/실제 파일 업로드 성공으로 기록하지 않는다.

# Verification Plan

- 기존 검증 전용 고정 버전 어댑터/엔진 필드와 실제 직렬화 형식을 확인한다.
- 5타입 유효 문서의 JSON 왕복과 타입/유한값/중복·잘못된 참조·숨은 필드/버전·경계 제한의 거부를 검증한다.
- 기존 빈 문서 생성/GET·Board/Shelf/Asset 회귀, 계약/생성 타입 검사를 루트 `VERIFY_BASE=32fbcd104c552216c44be878bfb4b8a4a3bbe879 make verify-plan` → `make verify`의 선택 범위로 실행한다.
- 관계형 스키마/저장 동작을 변경하지 않으므로 별도의 PostgreSQL migration/경쟁 저장은 이번에 완료했다고 설명하지 않는다.
- 실제 PR Type/라벨/ready·base/head/이슈 링크와 정상 커밋/푸시 훅을 확인한다.

# Impact

빈 문서 응답은 호환된다. 비어 있지 않은 본문의 구조 계약이 명확해지지만 현재 작성 입력 API는 아직 없다. 고정 버전 엔진은 기존 검증 후보의 직렬화 경계이며 제품 편집기 채택/통합 완료를 뜻하지 않는다. 기존 Board·회원 운영 API와 DB·파일 저장 로직을 변경하지 않는다.

# Loop Alignment

기존 요청 → CanvasService → 모델의 본문 검증 → 응답·생성 타입 루프를 구체화한다. 새 관계형 쓰기·도메인 이벤트/worker·실시간·UI/데스크톱 복구 루프는 변경하지 않는다. 저장/CAS·현재 권한 재검사/에셋 참조의 원자적 반영은 후속 #7에서 연결한다.

# Verification

구현 전 계획을 기록했다. 대상 단위/Canvas API 130검사가 통과했다. 최종 결과와 이번 작업의 생략 사유는 루트 검증 후 갱신한다.

최초 루트 검증은 백엔드 그룹 통과(282.6초, 988 통과/PG opt-in 1 skip)·프런트 단위 209 통과 후 기존 관리자 데모 1440/dark의 즉시 너비 비교가 실패했다(249 통과/1 실패). debug-live 절차의 디버거 상태 조회는 응답하지 않아 중단했고 실제 Chromium DOM을 4회 관측했다. 1회에서 같은 폰트/클래스 상태의 첫 측정 1157px가 다음 프레임의 848px로 바뀌어 데모 848px와 일치했다. 제품 코드에 로그를 넣지 않았고 실패 화면은 Playwright 산출물로 확인했으며 DOM 관측은 `.git/canvas-object-schema/layout-observations.json`에 보관했다. 원인은 페이지 이동 후 행 표시만 기다리고 배치 완료 전에 한 번만 비교하던 검사 시점이다. 비교 대상/값/허용 오차를 바꾸지 않고 두 관리자 경로의 `expect.poll(geometry).toEqual(...)`만 보완했다. 대상 관리자 데모 파일을 2회 반복한 12검사가 통과했다(10.7초). 이 추가 범위는 검증 중 발견 후 기록한 것이며 최초 계획에 있었던 것으로 표현하지 않는다.

두 번째 검증에서도 백엔드 988개는 통과했다(297.05초). 관리자 배치 비교는 통과했지만 기존 캡슐 hover의 DOMRect 높이 비교에서 32와 31.999969482421875의 차이로 브라우저 249 통과/1 실패였다. 실패 산출물은 `.git/canvas-object-schema/hover-*`에 보존했다. 이 비교만 소수점 3자리로 바꿔 0.000031px 수준의 좌표 계산 오차를 처리하고 실제 픽셀 크기 변화의 거부를 유지한다. 색상/대비·다른 비교의 허용 오차는 변경하지 않는다.

최종 `VERIFY_BASE=32fbcd1 make verify-plan`은 19개 변경 파일에 전체 15명령을 선택했다. 같은 기준 `make verify`는 **294.9초, jobs=2로 15명령 모두 통과**했다. 로그는 `.git/verification-logs/run-q6n5l934`, 실행 요약은 `.git/canvas-object-schema/verify-complete.log`다. 백엔드 988 통과/PG opt-in 1 skip(기존 경고 37), 프런트 단위/통합 209·브라우저 250·production 18·style-studio 3 통과와 Ruff/아키텍처·계약/생성 타입·설정/하네스·빌드/패키징을 확인했다. 캡슐 대상 5회 반복도 통과했다(5.8초).

자동 분류기가 공유/불명확 변경으로 전체를 유지하고 테스트 파일 수정 때 전체 소스 hash를 갱신해 재검증했다. 범위를 수동 강등하거나 실패 검사를 생략하지 않았다. 최종 성공 후 소스/문서/계약을 더 바꾸지 않고 작업 결과만 이 worklog에 기록한다. 정상 commit-msg/pre-push·실제 ready PR 메타데이터/거버넌스와 원격 게시 상태는 PR/이슈에서 이어서 확인한다.

수동 경계 검토에서 새 SQL/세션·트랜잭션/ORM 쓰기와 서비스/라우터 변경이 없고 구조 검증은 기존 models/canvas.py에 머무름을 확인했다. 기본 빈 문서 JSON과 현재 endpoint 집합은 유지되며 Content 객체 5타입·고정 필드/참조/순서의 OpenAPI와 생성 타입을 동기화했다. 변경한 한국어 문서의 로컬 상대 링크와 git diff --check도 통과했다. 관계형 저장 동작 변경이 없어 실제 PostgreSQL/마이그레이션·새 PUT/CAS/권한 회수·Asset 참조 원자 갱신은 이번에 검증했다고 설명하지 않는다. 제품 편집기 채택·실기 입력/신규 UI·운영 배포/실제 Actions도 후속이다.

# State Ownership

프런트 런타임 변경 없이 생성 타입만 동기화한다. 편집 상태 소유권은 이번 범위 밖이다.

# Memoization

프런트 런타임을 변경하지 않아 해당하지 않는다.

# Performance Evidence

요소/문서 크기 제한은 검증 상한이며 성능 보장 수치가 아니다. 실제 실행 결과와 한계는 검증 후 기록한다.

# Page Family

## Family

화면 변경 없음.

## Reference

기존 Content Canvas 포맷과 독립 검증 어댑터를 참조한다.

## Shared Rules

기존 한국어 문서·단일 저장소·도메인 모델/저장소 책임과 계약 동기화 규칙을 따른다.

## Exceptions

없음.

## Evidence

UI/페이지 구성과 상태를 변경하지 않아 화면 비교는 해당하지 않는다.
