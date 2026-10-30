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

## 작업 절차와 저장소 스킬

운영 절차는 아래 저장소 스킬을 읽고 따른다. 클라이언트가 자동 발견하지 않아도 해당 작업 전에 직접 읽는다.

| 작업 | 절차 |
| --- | --- |
| 커밋 준비·생성 | [b4-commit](.agents/skills/b4-commit/SKILL.md) |
| PR 생성·수정·요청된 병합 | [b4-pr](.agents/skills/b4-pr/SKILL.md) |
| GitHub 이슈 생성·갱신 | [b4-issue](.agents/skills/b4-issue/SKILL.md) |

커밋만 요청받으면 PR·이슈·병합까지 범위를 늘리지 않는다. 구현 작업은 사용자가 게시를 제한하지 않았다면 커밋·푸시·ready PR까지 마무리한다. draft는 사용자 요청이나 명시적 차단 사유가 있을 때 사용한다. 리뷰만 요청한 경우 파일 게시를 요구하지 않는다.

## 작업 불변 조건

- 시작 시 git status --short로 기존 변경을 보존한다. 구현 전에 <type>/<short-kebab-title> 브랜치와 .github/WORKLOG_TEMPLATE.md 기반의 다음 worklog/NNNN-description.md를 만들고 계획·설계·루프 영향을 먼저 쓴다. 사후 기록을 사전 계획으로 표현하지 않는다.
- 모든 작성 커밋은 Conventional Commit 제목과 비어 있지 않은 Changes:, Affected Files:, Verification: 본문을 갖는다. 한국어 설명과 자동화 토큰을 유지한다. 각 커밋은 Commit Title이 정확히 일치하는 완전한 worklog를 포함한다. 통합 merge commit은 제외한다.
- 루트 make verify-plan → make verify를 따른다. 브랜치 전체는 VERIFY_BASE=<기준 커밋>으로 지정하고 범위·확대·receipt 정책은 [검증 문서](notes/verification.md)가 소유한다. 불명확한 범위를 수동 강등하지 않는다. 실제 결과와 작업별 생략 사유를 기록하고, 같은 성공 검증을 반복하지 않는다. 과거의 생략 요청을 이후 변경의 영구 면제로 해석하지 않는다.
- make init은 env와 루트 훅을, make install은 잠금 의존성을 준비한다. 기존 환경·시크릿을 보존한다. commit-msg/pre-push 훅을 우회하지 않는다. 기존 custom hooksPath는 명시적으로 조정한다. [로컬 훅](notes/local-hooks.md)을 따른다.
- PR 제목은 [type] 한국어 설명이다. 필수 본문 섹션은 Summary, Scope, Reason, Verification, Documentation, Risk / Impact이며 한국어로 작성한다. PR Type·실제 라벨·관련 이슈·base/head·draft 상태를 직접 확인하고 실제 메타데이터로 PR_NUMBER=<번호> make git-governance-pr-check를 실행한다. 검사 통과가 라벨이나 병합 상태를 보장하지는 않는다.
- 이슈 제목은 [feat], [fix], [chore], [docs], [test], [perf] 등 영어 타입 접두사를 쓴다. 설명·본문·체크리스트는 한국어다. GitHub의 기존 양식을 사용하고 실제 완료 범위만 체크한다.
- 기본 병합은 merge commit이다. squash/rebase는 사용자 명시 요청만 허용한다. 자동 병합 등록 뒤 실제 방식·결과를 확인한다. 원격 보호 규칙은 관리자 권한과 작업 승인이 있을 때만 바꾼다. 수동 Actions와 로컬 훅을 서버 CI 보장으로 설명하지 않는다.
- 기본적으로 main 직접 푸시·삭제·이력 재작성은 금지한다. 사용자가 특정 리베이스의 원격 main 교체를 명시 승인한 경우에만 로컬 Git approvals의 기존/새 SHA·최신 upstream 기반·원격 백업을 pre-push 훅이 검증한 뒤 정확한 기존 SHA의 force-with-lease로 교체한다. 승인 없는 교체·삭제와 훅 우회는 계속 금지한다.
- 소스·계약·문서를 같은 브랜치/커밋/PR에 반영한다. 변경된 구조·동작·규칙의 한국어 문서와 진입 링크를 동기화하고 과거 worklog는 수정하지 않는다.

## 설계 루프

백엔드는 요청 → 라우터 → 서비스 → 모델/저장소 → 응답과 도메인 이벤트/작업 경계를 따른다. 프런트엔드는 페이지 → 도메인 훅 → 타입 기반 API → 상태 → UI 및 실시간 복구 루프를 따른다. 데스크톱 복구는 해당 타깃을 선택할 때 적용한다. 이번 변경에서 해당 없는 루프는 이유를 기록한다.

공용 UI와 상태·성능 규칙은 src/frontend/notes/react-performance.md 및 page-families.md를 따른다. 새 상태 라이브러리나 무차별 memo를 도입하지 않는다. 계약은 contracts/openapi.json과 src/frontend/contracts/openapi.json을 명시적으로 동기화하고 생성 타입을 검증한다.

## 초기화와 후속 작업

기본 초기화 재개 시 PROJECT_BRIEF.md, project.json, 현재 diff와 감사 근거를 읽고 미완료 단계부터 진행한다. 명시적으로 보류한 화면·브랜드·네이티브·제공자 연동을 임의로 구현하지 않는다. 프로젝트 설정은 make project-plan → make project-init → make project-check 순서이며 기존 env/시크릿을 보존한다. 상세 범위는 PROJECT_ONBOARDING.md 및 PROJECT_ONBOARDING_AUDIT.md를 참고하되 사용자 지정 범위를 우선한다.


## 백엔드 책임 경계

모델/저장소가 SQL·세션·트랜잭션·ORM 저장 필드 변경과 SQLAlchemy/드라이버 오류 변환을 소유한다. 라우터·서비스·인증 의존성은 DB 세션을 획득하거나 전달받아 CRUD/트랜잭션을 실행하지 않으며 임의 헬퍼로 우회하지 않는다. 서비스는 저장소 결과·도메인 예외나 보상 처리용 명시적 저장소 실패 계약을 사용하고 DB 제약 이름/error.orig를 해석하지 않는다. Redis는 제외한다. core의 인프라 상태 점검과 admin 엔진 메타데이터 조회는 업무 CRUD가 아니다. 트랜잭션 불변식과 commit 성공 여부가 불확실할 때의 정리를 유지한다.

상세 기준은 src/backend/BACKEND.md를 따르고 시작·완료 시 수동 검토한다. 기존 자동 경계 검사가 모든 규칙을 보장하지는 않는다. main.py 요청 핸들러를 포함한 라우터→서비스 호출, 도메인 Exception/ErrorCode, 서비스 간 비공개 메서드 접근도 점검한다. 업무 흐름과 기능 권한은 서비스/공유 가드가 담당하고 비공개 구현을 다른 서비스의 인터페이스로 쓰지 않는다. 순수 기술/전송 유틸, HTTP AuthService/SSE Request 어댑터의 직접 호출은 허용하며 이를 위한 불필요한 서비스·DTO를 추가하지 않는다. 동일 정책 상수는 공유하고 오류 enum/HTTP 상태 상수를 사용한다. 책임 위반·일관성 정리·허용 설계를 구분해 검토한다.
