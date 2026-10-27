# Commit Title

docs: 기본 회원 등급을 뉴커머 피너 큐레이터로 정한다

# Changed File Scope

- notes/community/README.md, domain-model.md, membership-policy.md, api-design.md: 기본 등급 이름과 정책 예제.
- notes/community/probes/scenario.json: 후속 구현용 기본 등급 표시명과 참조 예제.
- PROJECT_BRIEF.md: 현재 기본 등급 결정.
- worklog/0274-default-member-grade-names.md: 계획과 변경 기록.

# Reason

사용자가 기본 등급으로 Newcomer → Pinner → Curator와 한국어 뉴커머 → 피너 → 큐레이터를 선택했다. Board별 이름 변경·권한 정책 편집 가능 여부를 명확히 한다.

# Design

rank 0/10/20의 기본 표시명을 변경한다. 등급 이름을 권한 코드로 사용하지 않으며 실제 멤버·정책은 불변 grade_id로 연결한다. Board별 등급 이름/순서 및 Shelf 액션 정책 편집을 유지하고, 운영 역할별 고정 권한표와 혼동하지 않게 설명한다. 과거 worklog는 수정하지 않는다.

# Verification Plan

문서·공개 fixture만 변경한다. 사용자 지시에 따라 기존에 완료한 전체 검증은 재실행하지 않는다. JSON 문법·등급 참조 일치와 diff만 확인한다.

# Impact

제품 런타임·DB·기존 회원 데이터·API 계약은 변경하지 않는다. 다음 Board 생성 구현에서 사용할 기본 등급과 시나리오를 갱신한다.

# Loop Alignment

서버·프런트엔드 실행 루프 변경은 없다. 도메인 권한 정책의 명칭과 설명만 정리한다.

# Verification

JSON 문법·기본 등급 이름/rank·회원/Shelf의 등급 참조 일치와 git diff --check 통과. 문서/fixture 포맷 정리. 기존 전체 검증은 사용자 지시에 따라 재실행하지 않았다.

# State Ownership

프런트엔드 런타임 변경 없음.

# Memoization

프런트엔드 런타임 변경 없음.

# Performance Evidence

이름·문서 변경이므로 성능 측정 대상이 없다.

# Page Family

## Family

제품 UI 변경 없음.

## Reference

기존 회원 등급 설계 문서.

## Shared Rules

표시명과 불변 grade_id, 운영 역할과 활동 등급을 분리한다.

## Exceptions

제품 화면·공용 컴포넌트 변경 없음.

## Evidence

문서·fixture 검토 결과를 Verification에 기록한다.
