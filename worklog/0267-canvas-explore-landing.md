# Commit Title

feat: 격자 캔버스 기반 둘러보기 랜딩을 구현한다

# Changed File Scope

프런트엔드 랜딩/Home 라우팅, 캔버스 카메라 훅·기능 컴포넌트, 공통 navbar 슬롯·CSS·KO/EN문구와 관련 검증/문서.

# Reason

사용자가 제시한 자유 배치된 사진·주제 제목·필기체 문구을 실제 첫 화면에 적용하고 배경 격자로 캔버스임을 명확하게 보이도록 요청했다. 상단 둘러보기/예시 콘텐츠 및 하단 도움말 문구를 삭제하고 브랜드를 큰 필기체로 표시한다.

# Design

기존 /home에 직접 주제별 예시 DOM을 배치한다. 최종 사용자 지시에 따라 글로벌 사이드바와 레이아웃 선택을 제거하고 유일한 minimal 셸을 사용한다. 네브바의 GitHub·문서·Buy Me a Coffee 링크/노출 조건과 프로필·인증 기능은 보존하며 배경이 투명한 floating 헤더로 배치한다. 배경 선 격자는 viewport 끝까지 채우고 카메라 이동은 유한한 world 경계로 제한한다. 툴팁에 단축키를 표시하며 하단 도움말 문구는 삭제한다.

canvas/canvasRules.ts가 ui/document surface 타입, 유한 크기 검증, 줌 범위(25~200%), 카메라 경계와 키보드 action을 소유한다. useCanvasCamera/useCanvasShortcuts/useCanvasSnapshot은 탐색 주제·저장 API에 의존하지 않는다. UI 메뉴는 2400×1600 고정 bounds를 전달하고 게시물 캔버스는 향후 문서 크기를 전달한다. 게시물 저장은 구현하지 않는다. 최종 사용자 지시에 따라 활성 캔버스에서 Ctrl/Cmd + +,-,0 및 Ctrl/Cmd+휠을 캔버스 확대·축소에 연결해 브라우저 기본 확대를 막는다. 두 손가락 스크롤은 이동, 트랙패드/터치 pinch는 확대·축소다. 다른 화면에서는 캔버스 리스너가 사라진다. html-to-image를 지연 로딩하여 내용/언어/테마가 바뀔 때만 전체 장면을 캡처하고 카메라 이동은 viewport 테두리만 갱신한다. 미니맵의 파란 채움은 없애고 중립 테두리로 위치를 표시한다.

최종 시각 방향은 사용자가 마지막으로 확정한 사진 기반 구성을 따른다. 방사형 카드/연결선을 제거하고 큰 Canvanity 워드마크와 6개 주제의 사진/타이포그래피를 직접 DOM으로 배치한다. Caveat와 Nanum Pen Script를 OFL 라이선스와 함께 로컬 제공하고 공용 필기체 토큰을 로고/캡션에 적용한다. 라이트는 따뜻한 종이색, 다크는 차콜 표면이며 브랜드 파란색을 유지한다. 사진은 라이선스를 확인한 Unsplash WebP를 로컬 제공한다. zoom/fit/focus는 RAF 보간으로 부드럽게 갱신하고 모션 감소 설정에서는 즉시 반영한다.

네브바·줌 컨트롤 캡슐과 미니맵 외곽 테두리/그림자를 제거하고 세로 줌 컨트롤을 미니맵 옆에 둔다. 주제 호버는 밑줄 대신 작은 scale 전환을 사용한다. world를 넓혀도 초기 콘텐츠 보기와 유한 world 전체 보기를 구분한다. 선택 주제의 실제 DOM 크기로 focus한다.

# Verification Plan

최종 요구에 따라 최소 25%·최대 200%를 고정하며 축소 시에도 사진·제목·필기체 문구를 유지한다. 설정 화면과 프로필 메뉴는 compact 밀도로 조정한다.

기본 마우스 동작은 클릭/선택이며 Space 홀드 중에만 이동한다. 해제·blur·탭 비활성화 시 임시 이동과 드래그를 종료한다. H/클릭으로 고정하던 이동 모드를 제거하고 이동 아이콘은 Space 상태 안내로 바꾼다. 캔버스 내 텍스트 선택·이미지 기본 drag를 방지하고 검색 입력은 그대로 편집한다.

카메라 순수 유틸 단위 검사, 브라우저 drag/zoom/fit/search/topicfocus·키보드·touch·모바일·테마·저감동작·인증/설정/역할별 메뉴·production 검사, make verify-plan → make verify. PR 실제 메타데이터/머지 방식 확인.

# Impact

첫 랜딩 UI와 탐색 상호작용만 구현한다. 게시물CRUD·편집기·저장·협업·DBmigration은 추가하지 않는다. DB스키마 검토는 사용자에게 별도 전달한다. 외부 커뮤니티 조사 내용은 저장소에 기록하지 않는다.

# Loop Alignment

UI구성은 기존공용UI를 조합하고 인증/프로필은 기존 훅과 상태를 재사용한다. 정적예시 탐색이므로 새 API/실시간·작업루프는 추가하지 않는다. 포인터카메라는 자체생명주기와 정리함수를 가진다.

# Verification

make verify-plan과 최종 make verify 전체 15개 명령이 158.3초에 통과했다(.git/verification-logs/run-_v2ub5hn). 백엔드 504개, 프런트엔드 단위/통합 204개, UI 221개, production 18개, 스타일 스튜디오 3개가 통과했다. Space 임시 이동·선택 방지·키 해제/blur 복귀·검색 Space 입력, 25~200% 줌·축소 중 문구 유지와 compact 화면의 정렬을 포함한다. 푸시 훅에서도 실제 HEAD로 검사한다. DB·Redis·시크릿과 운영 배포는 변경하지 않았다.

# State Ownership

기존 AuthProvider/config가 인증·역할/기능을 소유한다. 탐색페이지가 검색·선택·조작모드를 소유하고 카메라 훅 ref가 viewport transform을 소유한다. 새 전역스토어와 서버상태복제는 없다.

# Memoization

정적인 주제 카드 묶음은 memo로 격리하고 stable focus callback을 전달한다. pointermove에서 React렌더를 발생시키지 않는다. 작은 조작버튼은 memo 추가효과가 없어 기존공용Button을 그대로 사용한다.

# Performance Evidence

production build와 모바일/데스크톱에서 팬·줌·넘침·키보드를 확인했다. 카메라 이동 중 미니맵 PNG URL이 유지되고 위치 테두리와 world transform만 프레임마다 갱신된다. 버튼 클릭의 중간 moving 상태와 최종 배율, 모션 감소 시 즉시 반영을 검증했다. 정적 주제는 memo와 안정적 callback 경계를 유지한다. 수치 성능 개선은 주장하지 않는다.

# Page Family

## Family

전역둘러보기 캔버스의 새랜딩유형. 공개브랜드와 공용컨트롤은 기존 /welcome와쇼케이스/설정타입을재사용한다.

## Reference

사용자 제공 중앙소개카드·주변6관심사이미지와 기존PublicNavbar/BrandBanner/Button/Modal/프로필메뉴를비교한다.

## Shared Rules

전역블루토큰·글꼴·공용버튼과 tooltip/profile의 포커스·모바일규칙을 유지한다. appearance는 app.css, 동적기하만 카메라훅에서 관리한다.

## Exceptions

최종 사용자 지시에 따라 전역 셸을 minimal로 통일한다. 설정/관리자 내부 섹션 탐색과 콘텐츠는 유지한다. 이전 sidebar/레이아웃 선택 전용 검사는 유일한 minimal 헤더/메뉴/테마/경계 검증으로 대체하며 공용 버튼·모달·대비·인증 검사는 유지한다. 화면 중앙의 예시콘텐츠는 신규편집기/게시물서비스의 동작을 의미하지 않는다.

## Evidence

실제 5173 서버를 모의 API로 격리해 라이트/다크 × 320/390/1440px를 확인했다. 화면 전체 격자와 기존 리소스 아이콘·필기체 워드마크를 유지한다. 캡슐·하단 안내·상단 라벨·미니맵 외곽 장식·파란 viewport 포커스를 제거했다. 줌/팬/fit/검색/요소 크기 기반 focus, touch pinch, trackpad Ctrl+wheel의 기본 이벤트 차단, Ctrl/Cmd 줌 키, hover scale, reduced motion을 Chromium으로 확인했다. Safari gesture 경로는 구현했으나 실제 Safari 하드웨어 핀치 검증은 포함하지 않는다.
