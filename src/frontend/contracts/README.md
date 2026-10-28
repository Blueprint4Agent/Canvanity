# Canvanity API 계약

타입 생성 입력은 이 디렉터리의 `openapi.json`이고 출처는 `source.json`입니다.
루트 `contracts/openapi.json`과 소비자 계약·생성 타입을 Canvanity의 같은 커밋/PR에서 갱신합니다.
출처의 `ref: same-commit`은 별도 저장소 커밋 pin이 아닌 현재 통합 변경을 뜻합니다.
루트 `make frontend-api-generate`로 타입을 만들고 `make verify-plan` → `make verify`를 실행합니다.
설치·빌드는 고정된 로컬 입력을 사용하며 실행 중인 서버에서 계약을 가져오지 않습니다.

현재 동작 기준은 같은 커밋의 루트 `contracts/README.md`와 도메인 구현 계약입니다.
경로·operation ID·에러 코드·쿠키/bearer 인증·OAuth 리다이렉트·readiness·SSE 동작이 같아야 합니다.
OpenAPI 일치만으로 런타임 호환성이 입증되지는 않습니다. 기존 refresh-token·realtime 제한은 유지합니다.
Spring Boot 구현 시 제공자 중립 계약 저장소로 승격할 수 있습니다.

## 관리자 사용자 목록

`GET /api/v1/auth/admin/users`는 DB 역할이 `admin`인 사용자만 접근합니다.
bootstrap 관리자도 같은 권한 검사를 적용합니다. `page`(1 이상), `page_size`(1~100,
기본 20), `search`(이름/이메일의 문자 그대로 검색, 최대 200자), `role`, `is_active`
필터를 지원합니다. 사용자 ID 내림차순 목록, 필터 결과 수와 전체 계정 통계를 반환합니다.
사용자 정보·역할·계정 활성/이메일 인증 여부·가입일·로그인 방식과 연결된 인증 수단 중
가장 최근 성공 로그인 시각을 제공합니다. 기록이 없으면 null입니다.
활성은 계정 사용 가능 상태이며 현재 접속 여부가 아닙니다. IP, 사용자 에이전트,
비밀번호, 토큰, 제공자 식별자는 제외합니다. 전체 로그인 이력이나 실시간 접속 추적이
아닌 조회용 스냅샷이며 역할 변경 API는 추가하지 않습니다.

## 결제 기반

추가된 `/api/v1/billing` 계약은 bearer 또는 앱 API 키 인증 설정, Stripe 제공 등록 세션/상태,
카드·Link 커서 목록을 정의합니다. `useBillingApi`는 자동 요청이나 캐시 없이 타입
API와 알려진 오류 코드 추출을 제공합니다. 결제 설정 화면은 작업별 UUID를 재시도에
재사용하고 상태 API의 `registered`를 확인하며 복귀·계정·연결 변경 시 재조회합니다.
[결제 UI](../notes/billing.md)의 예시 플랜과 현재 제한을 참고하세요. Stripe.js는 추가하지 않습니다. Stripe가 상태 원본이며
웹훅·실시간 알림·실제 청구 기능은 포함하지 않습니다.
