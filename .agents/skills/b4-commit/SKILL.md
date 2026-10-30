---
name: b4-commit
description: Canvanity 커밋을 준비하거나 생성할 때 작업 기록, Make 검증, 스테이징 거버넌스 절차를 적용한다.
---

# Canvanity 커밋

대상 Git 루트를 먼저 확인한다. 아래 경로와 명령은 모두 그 루트 기준이다.
AGENTS.md와 실제 diff·브랜치·기존 worklog를 읽고 관련 없는 변경을 보존한다.
src/frontend도 같은 저장소의 일반 디렉터리이므로 같은 작업/커밋에서 관리한다.

1. 구현 전에 작업 브랜치와 계획 worklog가 만들어졌는지 확인한다. 누락했다면 사실대로 기록한다.
   섹션 원본은 .github/WORKLOG_TEMPLATE.md이며 별도 양식을 복제하지 않는다.
2. 구현·문서와 해당 도메인 루프를 검토한다. 루트 make verify-plan → make verify를 실행한다.
   전체 브랜치는 VERIFY_BASE=<대상 기준 SHA>로 지정하고 notes/verification.md의 범위·재사용을 따른다.
   실패 요약을 읽고 원인을 고치며 검사를 우회하지 않는다.
3. 실제 결과·선택 범위·생략 이유·영향을 worklog에 쓴다. 한국어 Conventional Commit 제목과
   worklog Commit Title을 정확히 일치시킨다. 허용 타입과 정확한 제목 제약은
   scripts/validate_git_governance.py가 기준이다.
4. 제목과 비어 있지 않은 Changes:, Affected Files:, Verification: 섹션을 UTF-8 임시 파일로 쓴다.
   문서 전용을 포함한 모든 작성 커밋에 본문이 필요하다. 대상 파일과 worklog만 스테이징하고
   git diff --cached를 검토한다.
5. COMMIT_TITLE='<제목>' COMMIT_BODY_FILE=<파일> make git-governance-check로 스테이징 스냅샷을 확인한다.
   관련 내용을 바꾸면 재스테이징/재검사한다. git commit -F <파일>을 사용하고 훅을 유지한다.
6. 커밋과 실제 검증 결과를 보고한다. PR 게시가 요청 범위이면 인접 b4-pr/SKILL.md로 이어가며,
   커밋만 요청받은 경우 여기서 끝낸다.

검사 규칙을 새 스크립트에 복제하지 않는다. 훅/receipt 문제는 notes/local-hooks.md를 읽는다.
