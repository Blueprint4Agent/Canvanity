# Commit Title

feat: 블루 버튼과 종이 질감 토스트를 공용화한다

# Changed File Scope

공용 Button/ButtonLink·ToastCard·ToastProvider, 프로필 메뉴 로그인 링크, Showcase, 스타일·검사·문서.

# Reason

새 사용자 예시의 블루 그라데이션 버튼과 종이형 토스트를 캡슐/둥근 사각형에 적용하고 별도 링크 스타일 때문에 누락된 로그인 버튼도 공용화한다.

# Design

버튼의 실제 동작과 기존 형태를 유지하고 공용 스타일에서 그라데이션·가독성·호버를 소유한다. 링크는 ButtonLink로 동일 클래스 규칙을 사용한다. ToastCard는 종이색·접힌 모서리·상태 아이콘을 공유하며 중립/성공/오류를 명시적으로 구분한다. 문구로 성공을 추측하지 않는다. Showcase도 현재 알림 하나를 교체하며 기존 호출은 중립 상태로 호환하고 확인된 성공/실패 호출만 상태를 전달한다.

# Verification Plan

루트 make verify-plan → make verify, 라이트/다크와 모바일/데스크톱의 실제 로그인 링크·공용 두 형태 버튼·드롭다운·토스트 및 대비·모션 감소 확인. 푸시 훅과 PR 메타데이터 검사 후 merge commit으로 병합한다.

# Impact

공용 시각 스타일과 선택적 토스트 상태 추가이며 인증·API·데이터베이스 변경은 없다. 링크의 키보드/라우터 의미와 토스트 자동 닫힘·포커스를 유지한다.

# Loop Alignment

공용 UI·Showcase를 먼저 확장하고 기능에서 합성한다. 기존 인증 도메인 훅을 보존하며 새 요청이나 실시간 구독은 없다.

# Verification

make verify-plan 및 make verify 15개 명령 통과(174.8초): 백엔드 504개, 단위 206개, UI 232개와 운영 경로·Style Studio·계약·초기화 검사. 이후 단일 Showcase 알림 교체와 링크 스타일 마감 변경의 check-app 및 단위 207개도 통과했다. 푸시 훅에서 최종 커밋의 전체 검사를 재확인한다. git diff --check 통과.

# State Ownership

토스트 표시 상태는 기존 Provider, 생명주기는 ToastCard가 소유한다. 상태 톤은 결과를 아는 호출자가 전달하고 ButtonLink는 상태를 소유하지 않는다.

# Memoization

기존 안정적인 Toast dispatch와 메모 경계를 유지한다. 단순 표현 컴포넌트에 새 memo/전역 상태를 추가하지 않는다.

# Performance Evidence

새 라이브러리·이미지 다운로드 없이 CSS와 기존 아이콘을 사용한다. 기존 토스트 교체/만료/소비자 렌더 검사와 성공→오류 미리보기 단일 교체 검사를 통과했다. 실제 로그인 링크 탐색과 Showcase 공용 표면 비교도 브라우저에서 통과했다.

# Page Family

## Family

공용 버튼·라우터 링크와 일시적 토스트 피드백.

## Reference

사용자 블루 그라데이션/종이형 토스트 이미지, 현재 로그인 메뉴와 Showcase.

## Shared Rules

Button과 ButtonLink의 클래스와 스타일을 공유하고 ToastPreview와 실제 알림에 동일한 ToastCard를 사용한다.

## Exceptions

위험 액션의 의미와 투명 캔버스 아이콘/사진 카드 변형은 유지한다. 일반 버튼은 기존 캡슐/둥근 사각형을 모두 유지한다.

## Evidence

라이트/다크 390/1440px의 버튼·드롭다운·토스트를 .git/brand-review/workspace-*.png에서 비교했다. 캡슐과 둥근 사각형, 로그인 메뉴 링크·흰색 화살표 및 상태 아이콘을 확인했다. 본문/투명 액션과 지정된 채움형 브랜드 팔레트의 검증 기준을 구분해 기록했다.

사용자가 지정한 연한 블루와 흰색 글자를 최종 팔레트로 유지한다. 해당 채움형 버튼의 색상 회귀 검사는 2.5 대비를 하한으로 사용하며 WCAG AA 충족으로 설명하지 않는다. 일반 본문/투명 액션/토스트의 기존 4.5 기준은 유지한다. 드롭다운 화살표도 버튼 글자색을 상속한다.
