# Commit Title

test: 설정 레이아웃 비교에서 소수점 오차를 허용한다

# Changed File Scope

src/frontend/tests/e2e/billing.spec.ts와 이 워크로그.

# Reason

푸시 전체 검사에서 245개 UI 중 1개가 32px와 31.999984741210938px 차이로 실패했다.

# Design

스타일 속성 비교는 유지하고 간격·너비는 소수점 첫째 자리 정밀도로 비교한다. 화면 동작과 CSS는 변경하지 않는다.

# Verification Plan

billing 브라우저 검사와 푸시 훅의 전체 검증을 실행한다.

# Impact

브라우저 소수점 좌표 계산 오차만 허용한다. API·데이터·배포 영향 없음.

# Loop Alignment

설정 화면의 레이아웃 비교 검사만 보완하며 요청·상태·실시간 루프 변경 없음.

# Verification

초기 푸시 검사에서 백엔드 전체와 UI 244개는 통과했다. 보완 후 billing 검사와 전체 푸시 검증 결과는 PR에 기록한다.
