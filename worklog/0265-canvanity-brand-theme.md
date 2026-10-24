# Commit Title

feat: 브랜드 아이콘과 블루 테마를 적용한다

# Changed File Scope

branding 원본/실사용 아이콘, project.json, 프런트엔드 공통 CSS 토큰, 웹/네이티브 아이콘, 활성 소개 미리보기 8개와 브랜드 문서.

# Reason

사용자가 제공한 파란 C 아이콘과 예시 캔버스 화면의 블루 팔레트를 현재 서비스 전반에 적용한다. 예시 페이지 구성과 캔버스 기능은 구현하지 않는다.

# Design

기존 project.json → project-brand 생성 경로와 BrandMark/BrandBanner 소비자를 재사용한다. 제공 원본을 보존하고 투명 배경의 실사용 아이콘을 생성해 라이트/다크 공통 사용한다. 기존 화면 셸/크기/간격/상태 소유자는 유지하고 라이트·명시 다크·시스템 다크의 공유 CSS 색상만 동기화한다. 색상 대비와 호버/포커스/로딩/오류 표면을 함께 확인한다.

# Verification Plan

make project-brand, 프런트엔드 설정/타입/공통 UI/테마/프로덕션 브랜드 검사, 라이트·다크 모바일/데스크톱 브라우저 실제 이미지 응답과 스크린샷 확인, make verify-plan → make verify. 로컬 env/DB는 변경하지 않는다.

# Impact

브랜드 자산과 테마만 바뀐다. API·DB·라우트·캔버스 레이아웃은 변경하지 않는다. 네이티브 아이콘은 소스 자산을 대치하며 실제 네이티브 패키지 빌드는 별도다.

# Loop Alignment

UI 구성 루프에서 기존 BrandMark/BrandBanner와 공통 CSS 토큰을 그대로 재사용한다. 요청/API/실시간/데스크톱 연결 루프는 변경하지 않는다.

# Verification

중간 전체 make verify 15개 명령 통과(208.4초): backend504, unit/integration212, UI253, production18, studio3 및 별도 브랜드 임시 빌드·계약·패키징.
정상 페이지별 셀렉터를 기다리는 최종 수동 스모크12개(390/1440, light/dark) 통과: 실제 PNG 응답/로드·제목·가로넘침 없음·OS자동dark 일치. .git/brand-review의 스크린샷과 results.json으로 확인했다.
활성 소개 스크린샷의 원본 B4A 로고 잔존을 발견해 모의 계정/API 기반 기존 UI 8개(en/ko)를 재촬영했다. 실제 계정·제공자 호출은 없으며 화면·라우트·기능을 추가하지 않았다.
최종 자산을 포함한 make verify-plan → make verify 전체 15명령 통과(234.0초, .git/verification-logs/run-1y8xwrbr). backend504/unit212/UI253/production18/studio3 및 계약·임시 브랜드 빌드·패키징 통과. 이후 게시 상태 설명 문서만 갱신했으며 make verify-light로 재검사한다. 푸시 훅은 실제 전체 브랜치 범위를 다시 검사한다. 네이티브 패키지 빌드와 새 캔버스 페이지 구현은 수행하지 않았다.

# State Ownership

테마 상태는 기존 useTheme, 브랜딩은 기존 project config가 소유한다. 새 상태/요청/스토어를 추가하지 않는다.

# Memoization

렌더링 구조나 props를 변경하지 않는 색상·자산 작업이므로 새 memo 경계는 필요 없다. 기존 최적화는 유지한다.

# Performance Evidence

실제 빌드/브라우저 검사로 아이콘 요청·렌더링·테마 선택 유지·오버플로를 확인한다. 성능 수치 개선은 주장하지 않는다.

# Page Family

## Family

기존 공개·인증·설정·앱 셸·쇼케이스 공통 브랜드/테마.

## Reference

기존 /welcome, /show-case, /login 및 설정 계열을 비교한다. 사용자 두 번째 이미지는 색상 참고로만 사용한다.

## Shared Rules

기존 셸·공용 UI·간격·타이포그래피·반응형 규칙을 유지하고 전역 색상 토큰과 로고만 변경한다.

## Exceptions

예시 캔버스의 도트 배경·툴바·게시물 카드는 구현하지 않는다. 네이티브 패키지 실행은 이번 웹 검증에 포함하지 않는다.

## Evidence

실제 /welcome,/show-case,/login의 라이트/다크·390/1440 스크린샷12개와 .git/brand-review/results.json으로 확인했다. 기존 셸·컴포넌트 구조는 그대로이며 색상 선언과 자산만 달라졌다. 반복 실행은 이후 자산/문서 갱신으로 입력이 바뀌었기 때문이며 동일 입력의 성공 검사는 receipt를 활용한다.

관련 이슈: https://github.com/Blueprint4Agent/Canvanity/issues/2 . 로컬 API/DB/시크릿은 수정하지 않았다.
