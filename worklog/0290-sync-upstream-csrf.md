# Commit Title

fix: 최신 upstream의 CSRF 보호와 CI 환경을 통합한다

# Changed File Scope

B4FastAPI PR #162의 refresh CSRF 백엔드·관련 회귀/문서·계약, B4React PR #101의 대응 인증 클라이언트/회귀를 편입된 src/frontend에 적용한다. PR #163·#164의 브라우저 runner/Python 준비도 같은 CI에 통합한다. Canvanity 단일 저장소·한국어·기존 커뮤니티 기능/지침을 유지한다.

# Reason

사용자가 B4FastAPI 최신 병합을 리베이스로 반영하도록 요청했다. 쿠키 refresh CSRF 계약과 프런트 handshake를 함께 맞추고, 별도 B4React gitlink가 아닌 편입된 파일로 통합해야 한다.

# Design

기준 main f7cc0bf, 마지막 upstream 57f6ea2, 새 upstream/main 0767d81(#162/#163/#164), 대응 B4React 63386ba/addd14a를 기록한다. 별도 작업 트리에서 rebase-merges 충돌을 해결한 뒤 기존 main과 최신 upstream의 통합 commit으로 반영해 이력을 보존한다. src/frontend gitlink 변경은 일반 디렉터리와 필요한 클라이언트 패치로 변환한다. 계약은 Canvanity 백엔드에서 재생성해 양쪽 snapshot/타입을 함께 갱신한다. 업무 DB 경계와 기존 역할/등급/에셋 정책은 보존한다.

# Verification Plan

본문/cookie CSRF 분기, bootstrap/refresh 세션·TTL·철회/CORS와 기존 인증·프로필·Board/Canvas 회귀를 확인한다. 프런트 bootstrap 헤더·실패 시 refresh 중단·요청 범위 토큰과 기존 자동 복구 루프를 검증한다. 브랜치 전체에 VERIFY_BASE=f7cc0bf make verify-plan → make verify를 실행한다. 충돌 표식/미병합 파일·원래 main과 경로별 차이·CI의 monorepo 명령·계약/생성 타입·실제 PR 타입/라벨/상태를 확인한다.

# Impact

쿠키 기반 refresh는 CSRF proof가 필요하므로 대응 클라이언트/백엔드를 함께 적용한다. 완전한 명시 JSON refresh 자격은 유지한다. SQL migration이나 새 제품 UI는 추가하지 않는다. main은 PR merge commit으로 통합하며 원격 upstream은 읽기 전용이다.

# Loop Alignment

인증 API 상태/세션 복구 루프에서 csrf bootstrap→refresh→기존 계정 snapshot 갱신 순서를 유지한다. 백엔드는 라우터→AuthService→Redis token 유틸·저장소 경계를 유지하며 업무 세션/SQL을 서비스로 이동하지 않는다. 새 도메인 이벤트·작업·화면 구성/데스크톱 전용 경로는 추가하지 않는다.

# Verification

시작 main f7cc0bf, upstream/main 0767d81(#162/#163/#164)을 기록하고 계획을 작성한 뒤 별도 작업 트리에서 rebase-merges 91단계를 완료했다(결과 6564e1b). 문서/계약 10경로와 src/frontend gitlink 충돌을 해결하고, 통합 과정의 한국어 진입점과 프런트 mock 충돌도 해결했다. 기존 관심사 mock과 새 CSRF mock을 모두 유지하고 이전 스킬/가이드·worklog 0289를 원래 main에서 보존했다. B4React 63386ba/addd14a의 인증/회귀 패치를 편입 파일에 적용했으며 독립 저장소나 gitlink를 만들지 않았다.

Canvanity 백엔드에서 계약을 다시 생성해 양쪽 snapshot과 생성 타입을 동기화했다. 기존 Board/Shelf/Canvas/Asset 모델·서비스, AGENTS/세 스킬·project.json·브랜드/라이선스는 원래 main과 동일하다. 실제 CI YAML의 수동 trigger·ubuntu-24.04·Python/uv 설치 순서와 submodules 없는 monorepo 체크아웃을 확인했다. 미병합 파일/충돌 표식 없음, git diff --check 통과.

VERIFY_BASE=f7cc0bf make verify-plan → make verify 전체 15명령 통과(402.2초, jobs=2, run-u01m5_id). 인증/공유 모델/CI/계약 변경에 따라 분류기가 전체 영역을 선택했다. 백엔드 902 통과·명시 PostgreSQL 1 skip, 프런트 단위/통합 209·브라우저 250·production 18·style-studio 3 통과. Ruff/아키텍처·타입·계약·설정/하네스·빌드/패키징도 통과했다. SQL 스키마/Board 저장 로직이 바뀌지 않아 opt-in 실제 PostgreSQL은 추가 실행하지 않았다. 실제 Actions 실행/운영 배포도 수행하지 않았다.

원본 CSRF 회귀는 세션별 proof·동시 bootstrap/TTL·철회·위조/세션 혼동·부분 cookie fallback/완전한 명시 자격·CORS를 확인한다. 프런트 회귀는 요청마다 현재 proof를 받아 credentials/header로 제출하며 bootstrap 실패 후 refresh를 호출하지 않음을 확인했다. 기존 인증/계정·커뮤니티 회귀와 함께 통과했다. 새 관계형 SQL/세션 접근이나 다른 서비스 private 호출을 추가하지 않았고 Redis 유틸·도메인 오류/영어 기본 메시지·기존 DI 경계를 유지했다. 정상 훅으로 커밋/푸시 후 실제 PR Type/라벨/base/head/ready 상태와 거버넌스를 확인한다.

# State Ownership

CSRF proof는 refresh 함수 호출 범위에만 보관한다. 별도 React 상태·영구/전역 세션 저장소를 만들지 않고 기존 인증 상태 소유권을 유지한다.

# Memoization

새 memo/cache를 추가하지 않는다. 기존 refresh 동시 요청/상태 소유 구조를 보존하고 토큰을 장기 캐시하지 않는다.

# Performance Evidence

필요한 CSRF bootstrap 요청 1개를 refresh 앞에 추가하며 실패 시 후속 refresh를 중단한다. 반복 retry/polling 루프를 추가하지 않는다. 전용 API 회귀 2개와 프런트 전체 209개 검사에서 순서/요청 횟수/실패 중단을 확인했다. 추가 렌더 상태나 UI 구성 변경이 없어 별도 렌더 벤치마크는 수행하지 않았다.
