# Commit Title

docs: 이슈 제목의 영어 타입 접두사를 명시한다

# Changed File Scope

AGENTS.md, AGENTS.ko.md, .github/ISSUE_TEMPLATE/*.md의 제목 기본값.

# Reason

사용자가 이슈의 분류 접두사는 영어로, 설명과 본문은 한국어로 작성하도록 명시했다.

# Design

Conventional type의 [feat]/[fix]/[chore]/[docs]/[test]/[perf]를 예시로 명시하고 기존 영문 분류도 동일한 소문자 타입 기본값으로 맞춘다. 라벨·템플릿 본문·코드 동작은 변경하지 않는다. 한국어 에이전트 문서 두 파일을 동기화한다.

# Verification Plan

영문 타입 기본값 10개와 AGENTS 동기화 확인, make verify-plan/verify, 스테이징 거버넌스 및 실제 GitHub 이슈 제목/PR 검사.

# Impact

향후 이슈 생성 제목의 타입만 통일하며 사용자 설명은 한국어로 유지한다. 기존 이슈 #1~#10도 원격 제목과 참조 본문을 동기화했다.

# Loop Alignment

문서·템플릿 메타데이터 변경으로 런타임/API/실시간/UI 루프는 해당 없다.

# Verification

AGENTS.md와 AGENTS.ko.md 동일성, 템플릿10개 영어 타입, 원격 #1~#11 제목의 영어 타입을 확인했다. 전체 make verify의 하네스/거버넌스 검사가 통과했다. 본 문서 작업은 브랜드와 별도 커밋으로 기록하고 추가 make verify-light와 스테이징 거버넌스 검사 후 완료한다. 런타임 변경은 없어 별도 UI 검사를 추가하지 않는다.

관련 이슈: https://github.com/Blueprint4Agent/Canvanity/issues/11 .
