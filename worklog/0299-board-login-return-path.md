# Commit Title

fix: 로그인 후 보드 상세 복귀 경로를 보존한다

# Changed File Scope

App 인증 라우트, LoginPage, 순수 복귀 경로 유틸과 단위/브라우저 검사, 프런트엔드 가이드.

# Reason

2026-10-27 리팩터링 분리 전 stash에 남은 로그인 복귀 변경을 별도 PR로 게시한다. 현재 main의 백엔드·계약은 이미 병합되어 있으며 해당 코드는 복원하지 않는다. stash 원본은 보존한다.

# Design

현재 main c9dea2b에서 시작한다. 기존 허용 경로와 /b/{slug}만 허용하는 순수 함수를 로그인 성공과 이미 로그인한 사용자의 인증 화면 가드가 공유한다. 외부 URL·다른 앱 경로는 /home으로 보낸다. 인증·토큰 수명주기·화면 스타일은 기존 구성을 따른다.

# Verification Plan

복귀 경로 허용/거부 단위 검사, 실제 브라우저 로그인 성공·기존 세션 가드·화면 확인을 실행한다. 루트 VERIFY_BASE=c9dea2b0bfae2478041a154bfc908c83058b9e05 make verify-plan 후 정상 make verify와 커밋/푸시 훅, 실제 ready PR 메타데이터/거버넌스를 확인한다.

# Impact

기존 미게시 변경의 독립 게시다. 백엔드/계약/DB와 신규 기능 범위를 추가하지 않는다. 두 번째 가입·탈퇴 UI PR이 이 복귀 경로를 사용한다.

# Loop Alignment

인증 API 상태의 기존 소유권을 유지하고 성공 결과의 내부 경로만 공유 함수로 판단한다. 기존 세션 가드도 같은 결정을 사용한다. 실시간/데스크톱 복구는 이 변경에 해당하지 않는다.

# Verification

- 경로 단위12개와 Chromium 가드2개/실제 이메일 로그인2개를 확인했다. 로그인 모의 응답은 기존 LoginPayload.user를 포함하며 실제 Sign in 제출 버튼을 사용한다. 초기 검사에서 잘못 지정한 테스트 selector를 실제 화면에 맞췄다.
- 390/1440px에서 로그인 요청은 각각1회이고 같은 /b/agent-lab에 도착했다. 공용 인증 대화상자 캡처를 직접 확인했으며 화면 넘침은 없다. 브라우저 API는 격리 mock이며 실제 백엔드 서버 결합 실행을 주장하지 않는다.
- 정상 verify-plan이 공유 경로의 불명확한 영향을 전체로 확대했고 make verify15명령이408.6초에 통과했다. backend1,368/선택 실행 PostgreSQL8 skip, frontend221/UI254/production18/style3 통과. DB 코드 변경이 없어 PostgreSQL 선택 검사는 이번 변경에서 별도 실행하지 않았다.
- React 검토: 기존 AuthProvider/라우터 소유권과 이벤트 처리를 유지하고 새 effect/state/store·추가 요청·memo를 추가하지 않았다. 새 단순 문자열 함수는 로컬 동작만 담당한다.
- 로그: .git/unpublished-prs/return-full.log, .git/verification-logs/run-mz7lc1az. 정상 staged governance·commit-msg/pre-push와 ready PR 게시를 이어 수행한다. 이 단계에서 병합은 하지 않는다.

# State Ownership

사용자/로딩은 기존 AuthProvider, URL next는 라우터가 소유한다. 새 상태 저장소를 추가하지 않는다.

# Memoization

상수 크기의 문자열 검사와 이벤트/라우트 분기이므로 memo가 필요하지 않다.

# Performance Evidence

추가 API 요청이나 상태 구독을 추가하지 않는다. 실제 브라우저의 단일 로그인 요청과 최종 경로를 확인한다.

# Page Family

## Family

인증 대화상자와 기존 Board 상세.

## Reference

기존 LoginPage/AuthDialogRoute와 BoardHomePage.

## Shared Rules

공용 인증 셸·Modal·입력·버튼과 AppLayout 전환을 유지한다.

## Exceptions

없음.

## Evidence

기존 인증/보드 브라우저 회귀254개와 로그인 실제 상호작용을 확인했다. .git/unpublished-prs/return-login-mobile.png와 return-login-desktop.png를 직접 열어 기존 공용 셸·입력·버튼과 모바일 경계를 검토했다.
