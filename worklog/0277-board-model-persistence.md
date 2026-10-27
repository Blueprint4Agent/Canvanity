# Commit Title

refactor: 보드 데이터 접근을 모델 Repository로 이동한다

# Changed File Scope

models/board.py의 Repository·트랜잭션, BoardService·권한 평가기 DI, 생성/조회/삭제 및 PostgreSQL 회귀, 계층 검사와 문서. 신규 가입/탈퇴 API·UI와 계약 변경은 이번 커밋에서 제외해 로컬에 보존한다.

# Reason

사용자 지시에 따라 Board 서비스에 직접 작성한 SQL·세션·저장·트랜잭션을 모델 계층으로 이동한다.

# Design

`models/board.py` 안의 BoardRepository와 BoardTransaction이 쿼리·행 잠금·추가/삭제·flush/commit·롤백 경계를 소유한다. 서비스는 주입받은 Repository를 호출해 현재 데이터를 얻고 권한/한도/상태를 판단한다. 권한 판정은 잠금이 유지되는 트랜잭션 문맥 안에서 실행한다. 기존 스키마·응답·원자성은 유지하고 모델에서 서비스를 import하지 않는다. Board 관련 범위만 변경한다.

# Verification Plan

기존 생성 롤백·동시 slug/한도·권한·삭제 검사를 유지한다. 서비스의 SQL/세션 직접 접근 금지 회귀를 추가한다. 루트 make verify-plan → make verify와 명시 PostgreSQL 격리 검사를 실행한다.

# Impact

기존 미커밋 기능·데이터·계약을 보존하며 별도 스키마 변경은 없다. 비 Board 도메인은 범위 밖이다.

# Loop Alignment

요청→라우터→서비스→모델 Repository→DB→응답 경계를 적용한다. 이번 이동은 백엔드 구조 변경이며 UI/실시간/작업 루프는 기존 변경을 유지한다.

# Verification

가입/탈퇴 변경을 포함한 원래 작업 트리는 별도 이름의 Git stash와 .git/board-refactor-only-backup에 보존했다. 이번 커밋은 기존 개설 기능의 계층 이동만 포함하며 API·DB 스키마·프런트엔드 계약은 바꾸지 않는다. 권한 평가를 서비스로 분리하고 DB 접근은 models/board.py에 둔다.

billing 제외 상위 계층 감사에서 deps.py의 API 키 SELECT/사용 기록 갱신과 commit/refresh를 확인했다. admin.py는 엔진 메타데이터, main.py는 시작/종료 인프라 경계다. 이 파일들은 수정하지 않는다. 리팩터링만 분리한 스냅샷의 최종 검증과 게시 근거를 아래에 기록한다.


- 리팩터링 단독 스냅샷에서 `VERIFY_BASE=75d9cc7 VERIFY_JOBS=1 make verify` 15명령 통과(328.9초, run-fvh0kajo). 백엔드 530 통과/명시 PG 1 skip, 프런트 단위 207, UI 250, 프로덕션 18, 스타일 편집기 3 통과. 별도 실제 PostgreSQL migration 왕복·복합 FK·slug/한도 경쟁·삭제 검사 통과. API 계약 변경 없음.
- 기존 권한 판정과 정지 보드 오류 응답을 유지하며 SQL·저장 경계만 이동했다. DB 세션/SQLAlchemy import의 서비스 재진입은 아키텍처 회귀로 거부한다. Git 거버넌스 검사 통과 후 기존 개설 PR #28에 이 리팩터링 커밋만 추가해 merge commit 방식으로 병합한다.
