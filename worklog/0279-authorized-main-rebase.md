# Commit Title

chore: 명시 승인된 원격 main 리베이스를 제한적으로 허용한다

# Changed File Scope

루트 Git pre-push 훅·회귀 검사, 한국어 AGENTS/로컬 훅 문서. 리베이스된 코드의 기능은 변경하지 않는다.

# Reason

사용자가 원격 반영을 명시 승인했다. 기존 훅은 main 푸시를 무조건 거부하므로 훅 우회 없이 승인된 이력 교체 한 건을 검증할 수 있어야 한다.

# Design

기본 main 푸시·삭제 거부를 유지한다. 예외는 Git 내부 approvals의 명시적 JSON 문서와 origin·기존 SHA·새 SHA·현재 upstream/main SHA·원격 백업 ref가 모두 일치할 때만 허용한다. 일반 커밋/깨끗한 작업 트리/검증 검사는 그대로 실행한다. 실제 푸시는 정확한 기존 SHA를 지정한 force-with-lease로 수행한다. 승인 문서는 특정 SHA 쌍에만 유효하고 원격 변경이나 다른 HEAD에는 재사용할 수 없다.

# Verification Plan

기본 main 거부, 승인된 정확한 HEAD의 검증 실행, 잘못된 SHA·없는 백업·다른 기반 거부를 실제 임시 Git 원격으로 검사한다. 루트 전체 검증과 governance를 실행하고 원격 main·upstream 조상·백업 SHA·stash 보존을 확인한다.

# Impact

승인 없는 동작은 그대로다. upstream은 계속 읽기 전용이고 원격 보호 규칙을 바꾸지 않는다. 명시 승인된 Canvanity main 교체만 진행한다.

# Loop Alignment

Git 작업 보호/검증 루프에만 해당한다. 제품 API·UI·실시간·DB 스키마 변경은 없다.

# Verification

사용자의 “원격 반영 진행” 승인을 근거로 계획했다. 원래 main 370a5e3을 원격 chore/canvanity-pre-upstream-rebase에 보존했다. 실제 검사/반영 결과를 추가한다.


훅 실제 Git 회귀 13개 통과. `VERIFY_BASE=upstream/main VERIFY_JOBS=1 make verify` 전체 15명령 통과(150.7초, run-ijokaqg0), 백엔드 530 통과/명시 PG 1 skip. 변경 없는 프런트 검증은 일치하는 기존 결과를 재사용했다. 이전 단계에서 실제 PostgreSQL 검사도 통과했다. 원격 보호 규칙은 조회만 했고 변경하지 않았다. 이번 사용자 승인은 원래 main 370a5e3에서 검증한 새 HEAD로의 교체에만 적용한다.
