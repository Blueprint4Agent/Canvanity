# Commit Title

feat: 보드 가입과 탈퇴 화면을 연결한다

# Changed File Scope

boardsApi, useBoardActions, BoardHomePage, 한국어/영어 문구와 Board 브라우저 검사·프런트엔드/개설 문서.

# Reason

리팩터링 분리 전 stash의 미게시 가입·탈퇴 UI를 현재 코드와 계약에 맞춰 독립 PR로 게시한다. 이미 병합된 백엔드·계약과 과거 계획 worklog는 복원하지 않는다. 원본 stash는 보존한다.

# Design

선행 PR #61의 80111ffb190f04ca1a124f4acace850bc74b7a56에서 시작한다. 공개/open/active 비회원의 가입, 일반 active 회원의 확인 후 탈퇴, 비회원의 같은 보드 로그인 링크를 기존 API/hook/Modal/Button에 연결한다. 성공 후 guarded home을 다시 읽고 오류와 busy·취소/계정 교체 처리는 기존 훅이 담당한다. 운영 역할과 활동 등급은 서버 응답을 따르며 Owner 탈퇴 버튼은 노출하지 않는다. 이번 요청은 ready PR 게시까지다.

# Verification Plan

390/1440px·라이트/다크에서 가입 실패/재시도·탈퇴 취소/실패/재시도·현재 회원 상태 재조회와 guest 링크/Owner 경계를 실제 Chromium+격리 API mock으로 확인한다. 프런트 타입/포맷 사전 검사 뒤 VERIFY_BASE=80111ffb190f04ca1a124f4acace850bc74b7a56 make verify-plan→make verify, 정상 governance/commit-msg/pre-push와 실제 ready PR/base/head를 확인한다.

# Impact

기존 작성 UI의 복원 범위다. API/DB/계약과 새 운영 화면을 추가하지 않는다. #61 이후 순서로 검토/병합할 수 있는 stacked PR이며 현재 main은 그대로 유지한다.

# Loop Alignment

BoardHomePage → useBoardActions → 생성 타입 기반 boardsApi → 서버 검사 → home 재조회 → 회원 상태/모달 갱신 루프를 유지한다. 실시간 신규 이벤트·데스크톱 복구 프로토콜은 변경하지 않는다.

# Verification

- 현재 main에 이미 있는 가입/탈퇴 API와 생성 타입을 사용하며 두 번째 PR의 상대 diff에는 백엔드/계약 변경이 없다. 복원 시 확인창을 보드/계정 변경에 맞춰 초기화하고 연결 불가 시 새 탈퇴 동작을 잠그도록 현재 훅 경계에 맞췄다.
- 생성 타입 일치/TypeScript와 대상 Chromium10개 통과(10.1초). 390/1440px·라이트/다크의 가입 실패/재시도, 탈퇴 취소0회·실패/재시도, 성공 후 서버 회원 상태 재조회와 Owner 탈퇴 버튼 비노출·guest 복귀 링크를 확인했다. 브라우저 API는 격리 mock이다.
- 정상 verify-plan이 공유 경로의 영향을 전체로 확대했고 make verify15명령424.4초에 통과했다. backend1,368/선택 실행 PostgreSQL8 skip, frontend221/UI259/production18/style3 통과. DB 코드가 바뀌지 않아 선택 PostgreSQL 검사는 별도 실행하지 않았다.
- React 검토: 서버 상태를 기존 훅에 유지하고 페이지에는 확인창 열림만 추가했다. 기존 요청 취소/계정 경계와 CommunityCanvas 내용 버전을 재사용하며 새 store/memo/컴포넌트 스타일을 추가하지 않았다.
- 로그: .git/unpublished-prs/membership-full.log, .git/verification-logs/run-hmblx73w. 정상 staged governance·commit-msg/pre-push 및 #61 기준 ready PR 게시를 이어 확인한다. 이번 요청에서 병합하지 않는다.

# State Ownership

서버 Board/member는 useBoardHome, 요청 busy/error/AbortController는 useBoardActions, 탈퇴 확인창 열림은 페이지가 소유한다. 회원 상태를 별도 클라이언트 저장소로 복제하지 않는다.

# Memoization

단순 컨트롤과 이벤트를 연결하므로 새 memo를 추가하지 않는다. 기존 CommunityCanvas contentVersion이 서버 상태 변경을 반영한다.

# Performance Evidence

성공 후 필요한 home 재조회만 사용한다. API 요청 횟수·취소 시 요청0회·재조회 후 회원 상태를 브라우저에서 확인하며 지연 개선을 주장하지 않는다.

# Page Family

## Family

Board의 CommunityCanvas 및 공용 확인 Modal.

## Reference

기존 BoardHomePage 개설/삭제 확인창·BoardPage의 버튼과 notes/page-families.md.

## Shared Rules

기존 Button/ButtonLink/InlineMessage/Modal·공용 스타일·카메라·미니맵을 재사용한다.

## Exceptions

없음.

## Evidence

전체 브라우저259개와 대상10개 통과. .git/unpublished-prs/membership-visuals의 모바일 라이트/데스크톱 다크 탈퇴 확인창 및 기존 다크 개설 모달을 직접 열어 공용 셸·버튼·폭·표면을 비교했다. 나머지 두 화면 모드도 같은 대상 브라우저 시나리오로 확인했다.
