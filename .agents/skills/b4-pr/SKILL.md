---
name: b4-pr
description: Canvanity PR을 게시·수정하거나 요청된 병합을 수행할 때 템플릿과 실제 메타데이터를 확인한다.
---

# Canvanity PR

Git 루트·원격 저장소·AGENTS.md와 .github/PULL_REQUEST_TEMPLATE.md를 확인한다.
백엔드와 src/frontend는 한 저장소다. 별도 프런트 PR·gitlink 갱신 절차를 사용하지 않는다.

1. 브랜치/상태·대상 브랜치·작성 커밋과 같은 head의 기존 PR을 확인한다. 같은 작업은 기존 PR을 갱신한다.
   커밋이 남아 있으면 인접 b4-commit/SKILL.md를 읽는다.
2. 템플릿으로 최종 동작과 근거를 설명한다. PR Type을 실제 변경에 맞게 선택하고 빈 placeholder를 제거한다.
   실제 관련 이슈만 연결하며 전체 범위를 해결한 이슈에만 Closes를 쓴다. 원격 라벨 목록을 확인해
   타입/영역 라벨을 적용한다. 예: 기능 enhancement, 문서 documentation, 수정 bug.
3. 제목은 [type] 한국어 설명이다. 정확한 제약은 scripts/validate_git_governance.py를 따른다.
   본문을 UTF-8 임시 파일로 쓰고 PR_TITLE과 PR_BODY_FILE을 함께 make git-governance-check로 확인한다.
   체크아웃 HEAD가 게시할 커밋인지 확인하고 미커밋 작업을 정리한다.
4. 정상 훅으로 현재 브랜치를 푸시한다. 기본 ready PR이며 draft는 사용자 요청/차단 사유가 필요하다.
   CLI 본문은 --body-file을 쓴다. 결과가 불확실하면 재시도 전에 원격 상태를 조회한다.
5. 실제 title/body/PR Type/labels/base/head/head SHA/draft/issue 링크를 확인한다.
   생성·수정 후 PR_NUMBER=<번호> make git-governance-pr-check를 실행한다. 검사기는 라벨·draft·이슈 연결의
   정확성까지 보장하지 않으므로 직접 확인한다. URL과 open/merged 상태를 구분해 보고한다.

## 요청된 병합

병합이 승인된 작업에서만 진행한다. 직전에 실제 메타데이터·리뷰/대화 차단 사유와 실제 PR 거버넌스를
재확인한다. 보호 규칙이나 관리자 권한을 우회하지 않는다.

기본 merge commit이며 적합한 경우 gh pr merge <번호> --auto --merge를 사용한다.
가능한 도구에서는 expected head SHA를 지정해 다른 커밋을 병합하지 않게 한다.
squash/rebase는 사용자 명시 요청과 MERGE_METHOD=<방식> ALLOW_NON_MERGE_METHOD=true make git-governance-check가 필요하다.
자동 병합 등록 뒤 autoMergeRequest.mergeMethod가 MERGE인지 확인한다. 잘못 등록됐고 아직 열려 있으면
등록을 취소하고 바로잡는다. 즉시 병합됐다면 pending이라고 하지 말고 실제 merge 결과를 확인한다.
검사가 실제 대기 중일 때만 watcher 하나를 사용한다. 수동 Actions 정책은 notes/local-hooks.md를 따른다.
