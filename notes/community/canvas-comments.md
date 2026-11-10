# Canvas 댓글

상위 [#26](https://github.com/Blueprint4Agent/Canvanity/issues/26)의 독립 단위 [#64](https://github.com/Blueprint4Agent/Canvanity/issues/64)다. [좋아요](canvas-likes.md) 다음으로 게시본에 댓글을 연결한다. 제품 UI·답글·알림은 별도다.

## 계약과 사용자 흐름

- `GET /canvases/{canvas_id}/comments`: 기본 visible 댓글을 최신순 `(created_at,id)`으로 반환한다. `limit=1..100`(기본20), `cursor`, `status=visible|all`을 받는다. all은 현재 활성 Board Owner/Admin/Moderator만 사용한다. 응답은 items/next_cursor와 현재 can_create다.
- `POST /canvases/{canvas_id}/comments`: 세션 회원의 현재 `create_comment` 정책으로 공백 제거 후 1..5000자 body를 등록한다. 201과 단건 Location을 반환한다.
- `GET /canvases/{canvas_id}/comments/{comment_id}`: visible/삭제 tombstone은 현재 게시본 읽기 권한으로, hidden은 현재 작성자 또는 Board 운영진만 읽는다. 없는/다른 Canvas 댓글·접근 불가 숨김은404다.
- `PATCH` 같은 단건: expected_revision과 body, 또는 status=visible|hidden 및 reason을 받는다. visible 본인 댓글만 수정하며 숨김/복원은 현재 Board 운영진만 한다. 운영진도 다른 작성자의 본문을 수정하지 못한다.
- `DELETE` 같은 단건: expected_revision을 받고 작성자 또는 현재 Board 운영진이 tombstone으로 바꾼다. 본문은 DB에서 비우고 응답 body=null로 반환한다. 같은 현재 revision의 반복 삭제는 no-op다.

GET은 optional Bearer, 변경은 세션 전용이며 모든 응답은 private,no-store다. API Key는 회원 자격을 부여하지 않는다. response의 edit/delete/moderate capabilities는 서버가 현재 상태로 계산한다. 작성자 수정은 현재 댓글 작성 등급도 요구하며 본인 삭제는 현재 활성 회원인 경우 허용한다. Board 보관은 읽기만 허용한다. 숨김 댓글 작성자는 단건 조회/삭제할 수 있지만 수정·복원할 수 없다. 공개 목록에는 숨김/삭제 본문과 개수가 포함되지 않는다.

## 현재 권한·경쟁·삭제

작성자도 미게시 초안에 댓글을 달거나 읽을 수 없다. 공개본/현재 visibility와 현재 Board/회원/읽기/Shelf 정책을 매 요청 확인한다. 차단·정지·게시 취소·휴지통 뒤에는 댓글도 같은404 경계다. 전역 앱 관리자 역할을 Board 운영 권한으로 사용하지 않는다.

Board→User→Canvas 잠금과 공용 Access/Permission을 재사용한다. 댓글 revision은 Canvas clocks와 독립이다. 변경은 권한 확인 후 CAS를 검사하며 stale/포화 revision은409, 같은 body/status는 no-op다. SQL/commit 실패는 저장소가503으로 변환한다. cursor는 버전·Canvas·사용자·목록 상태에 결합하고 매 페이지 현재 권한을 다시 적용한다. 페이지 크기는 바꿀 수 있고 삭제 tombstone의 정렬 좌표는 보존한다.

0032는 댓글 테이블과 page/author/moderator 인덱스만 추가한다. 숨김에는 마지막 운영자/사유를 저장하고 삭제에는 본문을 남기지 않는다. 계정 삭제는 author/moderator를 SET NULL, Canvas/Board 영구삭제는 CASCADE로 정리한다. 작성자가 사라진 숨김 댓글도 익명에게 노출되지 않는다. 게시 취소·재게시/휴지통은 댓글 상태를 보존하며, 삭제 tombstone을 복원하는 API는 제공하지 않는다. 댓글이 남은 downgrade는 거부한다.

## 검증과 게시

API/SQLite의 형식·세션·CAS/no-op·현재 회원/운영진·숨김/삭제·페이지 경계/커서·게시 수명주기·rollback·계정 삭제와 실제 PostgreSQL migration/동시 수정·FK/자료 보존을 검사한다. 실행 결과/ready PR/main 반영은 [worklog0302](../../worklog/0302-canvas-comments.md)와 이슈/PR에서 구분한다. 운영 DB migration/배포는 별도다.
