# Canvas 조회·활동 통계

상위 [#26](https://github.com/Blueprint4Agent/Canvanity/issues/26)의 독립 단위 [#66](https://github.com/Blueprint4Agent/Canvanity/issues/66)다. [좋아요](canvas-likes.md)·[댓글](canvas-comments.md)의 실제 관계와 일 조회 원본을 집계한다. 제품 UI·추천 모델·자동 승급·인기순 Feed/Smart Shelf 적용은 별도다.

## 조회와 기록 계약

- `GET /canvases/{canvas_id}/stats`: optional Bearer로 현재 읽을 수 있는 게시본의 like_count, 현재 visible comment_count, view_count, activity_score, window_days/window_started_on/as_of를 반환한다. GET은 조회 원본을 만들지 않는다.
- `PUT /canvases/{canvas_id}/view`: 활성 세션의 현재 읽기 권한으로 계정·Canvas·UTC 날짜별1회 기록하고 `{recorded, stats}`를 반환한다. 같은 날짜의 재요청은 recorded=false, 다른 날짜는 별도 기록이다. API Key는 세션으로 사용하지 않는다.

모든 응답은 private,no-store다. Board/회원 제재·private 자격·현재 Shelf 읽기·Canvas/publication visibility·게시 상태를 매번 확인한다. 미게시 초안은 작성자도 통계를 읽거나 기록할 수 없다. 게시 취소·휴지통·접근 불가 객체는404다. archived Board는 읽기와 일 조회 기록을 허용하며 좋아요/댓글의 변경 정책은 각 계약을 따른다. 조회자 명단이나 계정별 원본은 공개하지 않는다.

## 기간·집계·활동 점수

기간은 오늘을 포함한 최근30개 UTC 날짜다. 시작일00:00 UTC부터 as_of까지의 신규 좋아요·현재 visible 신규 댓글을 사용하고 일 조회는 시작일..오늘 사이만 포함한다. 미래 날짜/시각 자료는 기간 집계에서 제외한다. 현재 좋아요/노출 댓글 수는 기간과 별개인 현재 전체 관계 수다.

`view_count`는 기간 내 **계정별 일 조회 수의 합계**다. 한 계정이 다른 날 다시 열면 각각 집계한다. 익명·IP·User-Agent는 수집하지 않으며 상세 열람 자체가 자동 집계를 일으키지 않는다. 제품 UI는 열람 시 명시적 기록 API를 연결하는 후속 작업이다.

`activity_score = 기간 내 현재 좋아요 + 기간 내 현재 visible 댓글 + view_count`로 각 활동을1점으로 합산한다. 좋아요 취소·댓글 숨김/삭제는 즉시 현재 집계와 점수에 반영되며 오래된 댓글 수정/숨김 복원이 생성 시각을 갱신하지 않는다. 동률 기준은 점수→게시 시각→Canvas ID 내림차순이다. 이는 후속 인기순 기능의 계산 기준이며 현재 Feed는 기존 latest 계약을 유지한다. 가짜 수치·비동기 근삿값은 넣지 않는다. 집계는 한 SQL statement에서 계산하므로 원본 변경이 다음 요청에 반영된다.

## 저장·경쟁·보존

0034는 `(canvas_id,user_id,viewed_on)` 복합 PK와 집계/만료/계정 삭제 인덱스를 추가한다. 원본 필드는 두 ID와 날짜 세 개뿐이다. 같은 Board 배타→현재 User 공유→Canvas 배타 잠금과 PK로 중복 기록·현재 정책을 보호한다. 읽기는 공유 잠금과 본문 JSONB를 제외한 공개 metadata를 사용한다. 모델이 SQL/세션/트랜잭션·오류 변환을 소유하며 서비스가 기간/점수 정책을 적용한다. 기록은 Canvas metadata/document/publication clocks를 변경하지 않는다.

Canvas/Board 영구삭제·계정 삭제는 조회 원본을 CASCADE로 제거한다. 게시 취소/휴지통은 원본을 기간 내 보존하되 통계 접근을 막는다. 자료가 남은 downgrade는 거부한다. commit 실패는503으로 전달하며 같은 날짜 재시도는 PK로 중복을 방지한다.

만료 날짜는 집계에서 즉시 제외한다. 물리 정리는 `canvanity.canvas_stats.cleanup`가 한 번에 최대1000개를 삭제하고 Beat가 매시간 발행한다. 중복 실행/이미 정리된 자료는 안전하며 로그에는 삭제 건수만 남긴다. worker의 이벤트 루프 종료 시 DB 자원을 정리한다. backlog가 있으면 후속 배치가 필요하다.

물리 정리에는 API와 같은 릴리스/DB 설정의 worker와 배포당 Beat 하나가 필요하다. 기존 [Celery 실행 가이드](../../src/backend/CELERY.md)의 `make celery-worker`, `make celery-beat` 또는 선택형 Docker 프로필을 사용한다. 메일이 비활성인 배포도 조회 원본 정리를 운영하려면 두 프로세스를 명시적으로 실행한다. worker/Beat가 멈추면 API 집계는 만료 자료를 제외하지만 원본 삭제는 실행되지 않는다. 이번 구현에서 환경/시크릿을 바꾸거나 운영 프로세스를 구동하지 않았다.

## 검증과 게시

API/SQLite·Celery 설정의 optional/세션·실제 관계 집계·UTC 일 중복/기간 경계·숨김/취소·GET 무기록·bounded 정리/rollback·계정/Canvas 삭제, 실제 PostgreSQL의 migration 보존/왕복·동시 기록 단일 원본·현재 제재/정리/FK를 검증한다. 실제 전체 검증/ready PR/main 반영은 [worklog0304](../../worklog/0304-canvas-activity-stats.md)와 이슈/PR에서 구분한다. 운영 DB migration/배포와 실제 worker/Beat 구동은 별도다.
