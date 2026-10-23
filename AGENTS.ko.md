# Canvanity 에이전트 가이드

Canvanity는 B4FastAPI를 포크한 캔버스 기반 커뮤니티다. PROJECT_BRIEF.md와 PROJECT_INITIALIZATION_AUDIT.md에서 현재 범위와 보류 항목을 먼저 확인한다.

## 저장소와 언어

- 백엔드와 src/frontend를 한 저장소에서 관리한다. 프런트엔드는 B4React에서 편입한 일반 디렉터리다. 별도 Git 저장소·서브모듈·자식 PR·gitlink 갱신을 사용하지 않는다.
- 소스·계약·문서 변경은 같은 작업 브랜치/커밋/PR에서 통합한다. Git 작업은 저장소 루트에서 수행한다.
- UI 기본 언어, 개발 문서, 사용자와의 대화, 커밋·PR 설명은 한국어다. 기존 영어 UI 전환은 유지한다.
- Conventional Commit 타입, kebab-case 브랜치, 자동화가 읽는 섹션 이름, 코드/API 식별자는 유지한다. AGENTS.ko.md는 이 파일과 동기화한다.
- project.json은 공개 이름·기능·언어 설정의 기준이다. 인증정보는 ignored env에만 두고 공개 문서/로그에 쓰지 않는다.
- origin은 Blueprint4Agent/Canvanity, upstream은 Blueprint4Agent/B4FastAPI다. upstream은 읽기 전용으로 취급한다. 라이선스·출처·기존 이력을 유지한다.

## 읽기 순서

1. 이 가이드와 PROJECT_BRIEF.md
2. 백엔드: src/backend/BACKEND.md, 테스트 변경 시 src/backend/TEST.md
3. 프런트엔드: src/frontend/AGENTS.md, FRONTEND.md, 테스트 변경 시 TEST.md
4. 설정/배포: PROJECT_SETUP.md, DEPLOY.md, notes/monolithic-deployment.md

도메인 문서의 원본 템플릿에 남은 별도 저장소/서브모듈 설명보다 이 저장소의 단일 저장소 규칙을 우선한다. 과거 worklog는 수정하지 않는다.

## 작업 순서와 검증

1. git status --short로 사용자 변경을 확인하고 보존한다.
2. 구현 전에 <type>/<short-kebab-title> 브랜치를 만든다.
3. .github/WORKLOG_TEMPLATE.md로 다음 worklog/NNNN-description.md를 만들고 계획을 먼저 쓴다.
4. 구현과 관련 한국어 문서·계약을 함께 수정한다. UI 변경은 기존 페이지/공용 UI를 먼저 확인한다.
5. 루트에서 make verify-plan 다음 make verify를 실행한다. 브랜치 전체는 VERIFY_BASE=<기준 커밋>으로 지정한다. 불명확한 범위는 전체 검사로 확대하며 수동으로 강등하지 않는다. VERIFY_FULL=1은 receipt 재사용 없이 전체 검사한다.
6. 결과와 생략 이유를 기록하고 대상 파일만 스테이징한 뒤 COMMIT_TITLE과 COMMIT_BODY_FILE을 지정해 make git-governance-check를 실행한다.
7. 로컬 commit-msg/pre-push 훅을 우회하지 않는다. 푸시/PR이 작업 범위이면 리뷰 가능한 PR을 만들고 실제 메타데이터를 PR_NUMBER=<번호> make git-governance-pr-check로 검사한다.
8. 기본 병합은 merge commit이다. squash/rebase는 사용자 명시 요청만 허용한다. 자동 병합 등록 시 실제 방식도 확인한다. main 직접 푸시·삭제·이력 재작성 금지.

make init은 환경 파일과 루트 Git 훅을 준비하며 make install은 잠금 의존성을 설치한다. frontend-init은 편입된 소스 존재만 확인한다. 성공한 내용 기반 검증은 24시간 내 동일 입력/환경/출력일 때만 재사용하며 CI와 VERIFY_FULL=1에서는 재사용하지 않는다. GitHub 워크플로는 수동 실행이며 로컬 훅을 서버 CI 보장으로 설명하지 않는다. 원격 보호 규칙 변경은 관리자 권한과 작업 승인이 있을 때만 한다.

## 커밋·PR·워크로그

- 커밋 제목 예: chore: 프로젝트 기본 설정을 적용한다
- 단순하지 않은 커밋 본문 필수 섹션: Changes:, Affected Files:, Verification:. 각 내용은 한국어로 쓴다.
- PR 제목 예: [chore] Canvanity 기본 설정 적용
- PR 본문 필수 섹션: Summary, Scope, Reason, Verification, Documentation, Risk / Impact. 각 내용은 한국어로 쓴다.
- 각 작성 커밋은 제목이 정확히 일치하는 worklog를 포함한다. 필수 섹션: Commit Title, Changed File Scope, Reason, Design, Verification Plan, Impact, Loop Alignment, Verification. 통합 merge commit은 제외한다.
- 프런트엔드 런타임 변경은 State Ownership, Memoization, Performance Evidence를 기록한다. UI 변경은 Page Family 비교와 실제 화면 검증도 기록한다.

## 설계 루프

백엔드는 요청 → 라우터 → 서비스 → 모델/저장소 → 응답과 도메인 이벤트/작업 경계를 따른다. 프런트엔드는 페이지 → 도메인 훅 → 타입 기반 API → 상태 → UI 및 실시간 복구 루프를 따른다. 데스크톱 복구는 해당 타깃을 선택할 때 적용한다. 이번 변경에서 해당 없는 루프는 이유를 기록한다.

공용 UI와 상태·성능 규칙은 src/frontend/notes/react-performance.md 및 page-families.md를 따른다. 새 상태 라이브러리나 무차별 memo를 도입하지 않는다. 계약은 contracts/openapi.json과 src/frontend/contracts/openapi.json을 명시적으로 동기화하고 생성 타입을 검증한다.

## 초기화와 후속 작업

기본 초기화 재개 시 PROJECT_BRIEF.md, project.json, 현재 diff와 감사 근거를 읽고 미완료 단계부터 진행한다. 명시적으로 보류한 화면·브랜드·네이티브·제공자 연동을 임의로 구현하지 않는다. 프로젝트 설정은 make project-plan → make project-init → make project-check 순서이며 기존 env/시크릿을 보존한다. 상세 범위는 PROJECT_ONBOARDING.md 및 PROJECT_ONBOARDING_AUDIT.md를 참고하되 사용자 지정 범위를 우선한다.
