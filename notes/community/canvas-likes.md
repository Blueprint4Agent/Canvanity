# Canvas 좋아요

상위 [#26](https://github.com/Blueprint4Agent/Canvanity/issues/26)의 독립 백엔드 단위 [#63](https://github.com/Blueprint4Agent/Canvanity/issues/63)다. 본문·metadata·publication revision과 별도 관계로 저장한다. 제품 UI·댓글·구독·조회/활동 통계는 별도 후속이다.

## 사용자 흐름과 계약

- `GET /api/v1/canvases/{canvas_id}/like`: 현재 읽을 수 있는 게시본의 `count`와 본인 `liked`를 반환한다. 익명은 `liked=false`다. optional Bearer이며 잘못된 토큰은 401, API Key는 회원 자격으로 쓰지 않는다.
- `PUT /api/v1/canvases/{canvas_id}/like`: 활성 세션과 현재 Board/Shelf `react` 권한으로 등록한다. 이미 등록했으면 행·시각을 바꾸지 않는다.
- `DELETE /api/v1/canvases/{canvas_id}/like`: 같은 현재 권한으로 취소한다. 없는 관계도 성공한다. 변경 두 경로는 200과 현재 `{count, liked}`를 반환한다.
- 모든 응답은 `Cache-Control: private, no-store`다. 좋아요 사용자 목록/신원은 제공하지 않는다.

초안 작성자도 게시하지 않은 Canvas에 좋아요를 등록하거나 집계를 읽을 수 없다. 공개본·현재 Canvas visibility와 현재 Board/Shelf 읽기 정책을 함께 적용한다. 비공개/정지/차단/등급 제한/게시 취소/휴지통은 단건 공개 조회와 같은 404 경계를 사용한다. 읽기는 가능하지만 현재 `react` 정책을 충족하지 못하면 변경은 403이다. Board 보관 상태는 읽기만 허용한다. 변경 때마다 재검사하므로 이전 토큰이나 이미 열린 화면이 권한을 유지하지 않는다.

## 저장·경쟁·수명주기

`0031_canvas_likes`는 `(canvas_id,user_id)` 복합 기본키, 계정 조회용 인덱스와 두 FK `ON DELETE CASCADE`를 추가한다. migration은 기존 자료를 수정하지 않으며 행이 남은 downgrade는 거부한다.

서비스는 공용 `CanvasAccessService`와 `BoardPermissionService`로 권한을 판단하고 저장소가 SQL/트랜잭션을 소유한다. 변경은 Board 배타 → 현재 User 공유 → Canvas 배타 잠금 순서를 사용한다. 같은 Board의 정책/회원/게시 상태 변경과 직렬화하며 동시 중복 PUT은 하나의 관계만 남긴다. GET은 Board/Canvas 공유 잠금으로 집계와 현재 권한을 유지한다. 이 잠금은 같은 Board 반응 쓰기를 직렬화하므로 큰 Board의 처리량 최적화는 별도 측정 후 다룬다. 본문 JSONB는 좋아요 조회에서 로딩하지 않는다.

게시 취소·재게시·휴지통은 좋아요 행을 보존한다. 공개 접근이 막히면 집계도 숨긴다. 복구/재게시 후에는 같은 관계를 다시 사용한다. 계정/Canvas 영구삭제는 관계를 제거하며 Board 영구삭제는 기존 Canvas 삭제를 통해 정리된다. 좋아요 변경으로 metadata/document/publication clocks나 게시 시각은 바뀌지 않는다. SQL/commit 실패는 저장소가 기존 Canvas 도메인 503으로 변환하며 부분 변경은 반환하지 않는다.

## 검증과 상태

API 계약, 실제 HTTP/SQLite 멱등성·개인 상태·현재 권한·게시 수명주기·commit 실패 rollback·Canvas 삭제와 격리 PostgreSQL migration/중복 제약·동시 요청·실제 잠금 대기 후 정책 재검사·계정 삭제를 검증한다. 루트 검증과 게시 상태는 [worklog0301](../../worklog/0301-canvas-likes.md) 및 이슈/PR을 따른다. 구현·로컬 검증·ready PR·main 병합·운영 배포는 각각 구분한다.
