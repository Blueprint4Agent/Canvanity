# Commit Title

feat: 캔버스 조회 집계와 활동 통계를 구현한다

# Changed File Scope

Canvas 조회 원본/통계 저장소·서비스·라우터·0034 migration, worker/Beat 정리, API/SQLite/PostgreSQL·Celery 설정 검사·양쪽 계약/생성 타입과 한국어 문서.

# Reason

2026-11-10 사용자 요청의 마지막 백엔드 단위 #66을 구독 PR #69/heade66ffc4 다음으로 구현한다. 구현 전에 feat/canvas-activity-stats와 이 계획을 만들며, #66에 집계/보존 계약을 먼저 기록했다.

# Design

GET /canvases/{id}/stats와 세션 PUT /canvases/{id}/view는 공용 현재 게시본/Board/Shelf/회원 읽기를 적용한다. PUT은 계정·Canvas·UTC 날짜별1회, GET은 조회 기록을 만들지 않는다. 원본은 두 ID와 날짜만 저장하며 IP/UA·익명 조회는 수집하지 않는다. 최근30개 UTC 날짜의 view_count, 현재 like_count/visible comment_count와 같은 기간 신규 좋아요+현재 visible 신규 댓글+일 조회의 activity_score(각1점)를 단일 SQL에서 계산한다. 동률 기준은 게시 시각/Canvas ID 내림차순이며 인기순 Feed/Smart Shelf 적용은 별도다. current Board/Canvas 잠금과 복합 PK로 중복/현재 정책을 보호한다. 계정/Canvas 영구삭제는 CASCADE다. 만료 원본은 통계에서 즉시 제외하고 기존 worker/Beat에 시간별1000개 정리를 연결한다. 물리 정리에는 해당 프로세스 운영이 필요하며 새 환경/제공자 설정은 바꾸지 않는다.

# Verification Plan

API/optional GET·세션 PUT·UTC 기간/일 중복·실제 좋아요/댓글 상태·정리 멱등/계정/Canvas 삭제·rollback·Celery 설정을 검사한다. 실제 격리 PostgreSQL에서 migration/보존·동시 기록·집계를 검증한다. 기준은 실제 구독 head e66ffc4e0fb1b1194c8e62e02d2e6ee7c2386953이며 verify-plan→verify·정상 훅/ready PR와 실제 거버넌스를 수행한다.

# Impact

조회 원본 테이블·API·정리 작업을 추가한다. Canvas clocks와 기존 공개 Feed 계약은 유지한다. 제품 UI·추천 모델·자동 승급·운영 DB migration/배포·실제 worker/Beat 구동은 별도다. #67 → #68 → #69 다음 의존 PR로 게시한다.

# Loop Alignment

요청 → optional/세션 → 현재 읽기 → 모델 소유 기록/단일 집계 → 응답. Beat → Celery → 서비스 → 모델 정리 → count 로그의 작업 루프를 적용한다. worker 이벤트 루프의 DB 자원 정리를 보존한다. 새 실시간/데스크톱/UI 상태는 해당 없음.

# Verification

- API/SQLite·Celery 설정9개10.50초 통과: optional 조회/세션 기록, GET 무기록·일 중복/다른 날짜·실제 좋아요/노출 댓글 점수·숨김/취소·기간/미래 날짜 제외·bounded 정리/반복·commit rollback·계정/Canvas CASCADE와 clocks 보존을 확인했다.
- 실제 localhost PostgreSQL 고유 schema 통계1개2.14초, 기존 Tag/layout/publication 회귀3개6.96초 통과했다. 동시 기록6건 중1건만 새 원본·집계 일치·최소3필드·현재 제재·기간/정리·계정/Canvas 삭제·migration 자료 보존/빈 왕복·자료 있는 downgrade 거부와 schema 제거를 확인했다.
- 책임 경계 수동 검토: 서비스는 현재 읽기와 UTC 기간/점수를 조합하고 SQL/ORM 쓰기·트랜잭션·SQLAlchemy 오류 변환은 모델 저장소가 소유한다. core task의 DB dispose는 worker 이벤트 루프 자원 정리이며 업무 CRUD를 수행하지 않는다. 다른 서비스의 비공개 인터페이스 호출은 없다.
- 실제 GitHub PR #69의 head e66ffc4를 기준으로 확인한 verify-plan은 모델/계약/공유 영향으로 전체15명령을 선택했고 make verify가613.6초에 통과했다. frontend221/UI259/production18/style3·아키텍처/계약/생성 타입·브랜딩/모놀리식 패키징을 확인했다. 신규 UI·인기순 Feed·추천·자동 승급·운영 DB migration/배포·실제 broker/worker/Beat 구동은 범위 밖이다. 정리 서비스와 스케줄 설정을 검사한 것과 운영 task 전달을 구분한다.

# State Ownership

조회 원본과 관계/집계는 DB, UTC 경계는 서버, 권한은 공용 정책이 소유한다. 프런트는 계약/생성 타입만 갱신한다.

# Memoization

프런트 런타임 변경 없음.

# Performance Evidence

본문 JSONB를 읽지 않고 집계를 한 statement로 계산하며 정리는 bounded batch다. 실제 중복/기간/보존 결과는 검증 후 기록한다.

# Page Family

## Family

해당 없음: 백엔드 API/작업 큐/계약.

## Reference

현재 Canvas 공개본/좋아요/댓글과 기존 asset cleanup worker.

## Shared Rules

공용 현재 정책·모델 소유 SQL/트랜잭션·기존 Celery 실행/환경을 재사용한다.

## Exceptions

없음.

## Evidence

API/SQLite·Celery 설정9개, 실제 PostgreSQL 통계1개/관련 회귀3개로 집계·권한·경쟁·보존을 확인했다. 신규 화면 변경은 없으며 전체 검증/게시 상태는 위 Verification을 따른다.
