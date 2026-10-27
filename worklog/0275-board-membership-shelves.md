# Commit Title

feat: 사용자 Board 개설과 기본 홈 흐름을 구현한다

# Changed File Scope

백엔드 Board 생성·기본 등급/멤버/Shelf/홈 모델·마이그레이션·서비스·라우터·생성/조회 권한 테스트, 양쪽 OpenAPI와 생성 타입, 프런트엔드 Board 목록·개설·기본 홈과 도메인 훅, 관련 한국어 문서. 이전 등급 이름 변경 0274를 보존한다.

# Reason

#22/#23의 첫 수직 흐름인 사용자 Board 개설부터 실제 데이터로 연결한다. 사용자의 추가 지시에 따라 회원/등급/운영진/Shelf 관리 화면은 다음 작업으로 두고 목록→개설→기본 홈을 우선한다.

# Design

기존 인증/공식 관심사/공용 UI를 재사용한다. Board·Owner·기본 Newcomer/Pinner/Curator 등급·정책·기본 Shelf·홈을 단일 트랜잭션으로 생성한다. UUID 소속 FK와 revision 충돌을 적용하고 공개/비공개 생성·기본 읽기/작성 정책과 조회 권한을 구현한다. 멤버 가입/수동 초대·등급 편집·운영진/제재·정책 편집·종료 경로는 후속 작업이다. 게시글/에셋/자유 홈 편집은 후속 이슈 경계다. 이전 스테이징된 이름 변경은 유지한다.

# Verification Plan

새 런타임/권한/마이그레이션 변경이므로 기존 검증을 그대로 재사용하지 않고 관련 테스트·PostgreSQL 격리 통합·실제 화면을 검증한다. 루트 VERIFY_BASE=75d9cc7e6b7cd6a2b74b97e1f95525af6d728988 make verify-plan 다음 make verify를 실행한다. 계약과 생성 타입을 동기화하고 governance를 검사한다.

# Impact

기존 계정·프로필 데이터와 시크릿은 보존한다. 신규 DB 스키마/API와 Board 화면이 추가된다. 네이티브·외부 제공자·운영 배포·자동 승급은 변경하지 않는다.

# Loop Alignment

라우터→서비스→모델/세션→응답, 페이지→도메인 훅→생성 타입 API→상태→공용 UI를 따른다. 실시간 push/작업은 이 단계에서 필요하지 않으며 요청 시 최신 권한을 검사한다.

# Verification

- 개설/조회/롤백/비공개/등급 정책/빈 보드 삭제와 API 계약을 단계별 검증했다. 실제 PostgreSQL의 전체 upgrade·복합 FK·slug 경쟁·19→20개 한도 경쟁·downgrade/re-upgrade 통과. 임시 schema 삭제 후 부재 확인.
- 실제 브라우저→격리 FastAPI/SQLite→DB 생성→홈→reload·무인증 공개 열람·비공개 차단 흐름 통과. `.git/board-creation-e2e/result.json`과 390/1440 light/dark PNG. 실제 env/기존 사용자 데이터 대신 전용 SQLite·메모리 Redis·로컬 파일을 사용했다.
- 기존 개발 8000 API/5173 목록도 읽기 확인했다. 기존 reload 프로세스의 미완료 종료로 응답이 지연되어 같은 env로 복구했고 graceful shutdown을 3초로 제한한 개발 명령으로 재기동했다. env/시크릿 변경 없음. 기존 PostgreSQL head는 0024이며 테스트 Board는 기존 DB에 만들지 않았다.
- 최초 root 검사에서 공개 GET의 OpenAPI optional security/세션 전용 목록 등록과 feature 컴포넌트의 직접 도메인 훅 호출을 지적했다. optional 인증을 명시하고 catalog를 페이지 소유 props로 바꾼 뒤 해당 검사 통과.
- 7 browser workers와 root jobs=2에서 UI 66개 시간 초과(179 통과/17.6분), 다른 실행에서는 Vitest 5개 시간 초과가 발생했다. 기존 해당 소스의 단위 207개는 이전 실행에서 통과했으며 당시 load average 22.70을 관측했다. 전체 범위/시간 제한을 줄이지 않고 browser/unit workers=2, root jobs=1로 재검증한다. 새 board-creation.spec.ts를 전체 UI 목록에 등록했다.
- 백엔드 전체 530 통과/1 skip(명시 실행하는 PostgreSQL 검사), 기존 Pydantic/Argon2 등 경고 유지. 최종 통합 결과는 다음 항목과 같다.

- 후속 전체 검사에서 단위 207개 모두 통과했다. UI 250개 중 생성 4개는 제거한 CSS 클래스 `board-active`를 찾던 테스트 오류였다. 실제 DOM은 `aria-current="page"`이고 개설·홈 이동은 정상이다. 테스트를 접근성 속성 기준으로 수정했다.

- 최종 `VERIFY_JOBS=1 VERIFY_BASE=75d9cc7e6b7cd6a2b74b97e1f95525af6d728988 make verify` 전체 15명령 통과(343.7초, run-faax0i62). 백엔드 530 통과/1 skip, 단위 207, 브라우저 250, 프로덕션 18, 스타일 편집기 3 통과. 생략/범위 강등 없음. 별도 PostgreSQL 검사는 기존 성공 결과를 사용한다.

# State Ownership

서버 aggregate revision/멤버 정책이 원본이다. 도메인 훅이 서버 로딩/변경/오류/계정 epoch를 소유하고 페이지는 폼 초안만 소유한다. 카메라 상태와 분리한다.

# Memoization

새 상태 라이브러리를 도입하지 않는다. 입력 상태를 캔버스 바깥에 복제하지 않고 검증된 공용 컴포넌트를 재사용한다. 필요한 안정 참조만 적용한다.

# Performance Evidence

실제 POST 201 후 홈 GET·reload GET을 확인했다. 목록 Interest는 일괄 조회하고 홈은 Shelf별 추가 조회 없이 정책을 묶어 평가한다. 폼 초안은 모달 안에 있어 타이핑으로 캔버스 미니맵을 다시 만들지 않는다. 새 상태 라이브러리/편집 엔진 의존성 없음.

# Page Family

## Family

Board 목록·기본 홈은 CommunityCanvas, 개설은 기존 공용 Modal 폼 계열.

## Reference

BoardPage·MyCanvasPage·SettingsPage·AdminPage와 기존 Modal/SectionNavigation/Button/Input.

## Shared Rules

기존 앱 셸·공용 UI·한국어 기본/영어 전환·모바일/라이트/다크·페이지 전환을 재사용한다.

## Exceptions

게시글이 없는 초기 상태는 빈 상태로 표시하며 예시 게시물을 실제 데이터처럼 표시하지 않는다.

## Evidence

독립 실제 서버의 390/1440 light/dark PNG를 시각 확인했다. 기존 CommunityCanvas의 유한 팬/줌·도구·미니맵을 유지하고 개설 모달은 기존 프로필 관심사/공용 폼과 동일하다. 모바일에서 캔버스의 일부 영역은 팬으로 탐색하며 문서 가로 넘침은 없음을 확인했다.
