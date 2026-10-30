# Commit Title

chore: 스킬과 하네스 운영 지침을 B4FastAPI와 동기화한다

# Changed File Scope

upstream PR #161의 .agents/skills/b4-commit·b4-pr·b4-issue, AGENTS/한국어 가이드·검증/프런트 통합 문서·PR 템플릿과 .agents 문서 분류 회귀. Canvanity 단일 저장소·한국어·PR 유형/라벨·명시 승인 main 보호 규칙을 유지하고 커뮤니티 구현/계약/프런트 런타임은 보존한다.

# Reason

사용자가 B4FastAPI의 최신 스킬·하네스 문서를 리베이스로 통합하고 충돌 해결 후 커밋·PR 병합까지 요청했다. 운영 절차를 재사용 가능한 저장소 스킬로 분리하면서 Canvanity의 별도 저장소가 아닌 프런트 구조와 기존 검증/추적 요구를 유지한다.

# Design

현재 main 6161fc1186a0c5742d1358bc3aee6dc36ec7d658, 기존 upstream 기반 ff11967, 최신 upstream/main 57f6ea2(PR #161, 작성 커밋 647700d)를 기록한다. 별도 작업 트리에서 Canvanity 이력을 rebase-merges로 최신 upstream 위에 재적용하고 문서 충돌을 해결한다. 검토한 최종 트리를 기존 main과 최신 upstream의 통합 merge commit으로 작업 브랜치에 반영해 원격 main 이력을 보존하고 PR diff를 실제 upstream 문서 변경으로 제한한다. 새 기능이나 DB/API 변경을 추가하지 않는다. 사용자 stash·환경 파일은 적용하거나 이동하지 않는다.

# Verification Plan

리베이스 미병합 파일·충돌 표식·upstream 조상·최종 트리와 원래 main의 경로별 차이를 검사한다. 단일 저장소/한국어/라이선스·주요 커뮤니티 소스·양쪽 API 계약·프런트 파일의 보존을 확인한다. 루트 VERIFY_BASE=6161fc1 make verify-plan → make verify의 선택 결과를 따르고 변경한 하네스 회귀와 실제 PR 유형/라벨·기준/head·거버넌스를 확인한다.

# Impact

최신 upstream 스킬/문서·문서 영역 분류를 가져온다. 실제 커뮤니티 동작·DB 스키마·UI·제공자/배포 설정은 변경하지 않는다. main에는 PR의 기본 merge commit으로 통합하며 upstream은 읽기 전용으로 유지한다.

# Loop Alignment

변경은 작업 계획→검증→커밋→PR 메타데이터→요청된 병합의 Git/하네스 운영 루프다. 제품의 백엔드 요청·이벤트/작업, 프런트 상태·실시간·UI 및 데스크톱 복구 루프는 기존 동작을 유지하고 새 경로를 추가하지 않는다.

# Verification

시작 트리는 깨끗했고 기존 main 6161fc1과 최신 upstream/main 57f6ea2를 확인했다. 작업 브랜치와 이 계획을 만든 뒤 별도 작업 트리에서 rebase-merges 86단계를 완료했다. 초기화 커밋의 문서 9개 충돌을 Canvanity 한국어/단일 저장소 기준으로 해결하고, 최종 통합에서 upstream의 절차 분리·범위별 검증·참조 문서를 반영했다. upstream/main은 리베이스 결과 ecf0cff의 조상이다. range-diff에서 기존 작성 커밋 22개는 패치 동일, 1개는 초기화 문서 충돌 해결 차이로 확인했다.

스킬 3개의 quick_validate 통과. 변경한 가이드의 로컬 링크·AGENTS.md/AGENTS.ko.md 일치·충돌 표식/미병합 파일 부재를 확인했다. 원래 main 대비 src/backend/app·tests·alembic, src/frontend 전체·양쪽 계약·project.json·branding·LICENSE의 차이는 0개다. 차이는 스킬/운영 가이드/PR 템플릿·분류기와 fixture·새 worklog 범위에만 있다. 과거 worklog는 변경하지 않았다.

VERIFY_BASE=6161fc1 make verify-plan → make verify 통과(15.0초, run-coktglnm). 선택 영역은 governance/harness, 실행은 make verification-harness-test 1명령이다. 검증 fixture 56개·Git 훅 13개·거버넌스 14개가 통과했다. 회귀의 의도된 실패 fixture 로그는 예상 분기를 확인한 것이며 suite는 모두 OK다. 백엔드/프런트/브라우저/빌드 검사는 앱·계약 변경이 없어 분류기가 선택하지 않았고 수동으로 범위를 강등하지 않았다.

실제 제품 루프는 변경하지 않아 런타임/상태/브라우저 실험을 추가하지 않았다. 스킬의 단일 저장소 경로·한국어 제목 허용·ready PR 기본값·실제 PR Type/라벨/상태 확인을 수동 검토했다. 정상 훅을 유지한 커밋/푸시·ready PR·요청된 merge commit 병합은 이어서 수행하며 실제 메타데이터를 확인한다. 기존 main 이력·사용자 stash/환경 파일을 재작성하지 않고 upstream은 읽기 전용이다.
