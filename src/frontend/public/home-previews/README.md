# Canvanity 소개용 UI 미리보기

현재 Canvanity 로고·블루 라이트 테마를 적용한 기존 UI를 Chromium 1360×900에서 촬영했다. 한국어·영어를 함께 갱신한다. 캔버스 서비스의 신규 화면이나 실제 계정/서비스 상태를 의미하지 않는다.

- components: /show-case 공용 UI 카탈로그.
- users: /admin 모의 example.com 계정과 역할.
- server: /admin/server 모의 연결/통합 스냅샷. 실제 운영 상태가 아니다.
- billing: /settings?section=billing 모의 계정과 테스트 카드 4242.

독립 브라우저의 /config 및 API 모의 응답은 기존 admin-panel/admin-server/billing 테스트 fixture를 기반으로 한다. 외부 요청을 차단하고 실제 계정·결제·엔드포인트·토큰을 사용하지 않는다. 운영 관리자 세션을 촬영하지 않는다. b4a_language와 blueprint4fastapi_theme=light를 설정하고 실제 표/연결행/테스트 카드가 표시된 뒤 Chromium의 WebP 캡처(quality86)로 저장했다.

브랜드는 루트 project.json → project-brand 생성 경로를 사용한다. 과거 B4A 로고가 포함된 래스터 이미지가 현재 서비스에 섞이지 않도록 이 8개 활성 미리보기도 갱신했다. 사용자 제공 캔버스 예시의 페이지 레이아웃은 구현하지 않았다.
