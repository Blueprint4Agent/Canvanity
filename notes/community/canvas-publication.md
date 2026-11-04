# Canvas 게시·게시 취소와 공개본 단건 열람 — #51 / #8

작성자가 명시적으로 게시한 metadata·본문·태그·이미지만 다른 사용자에게 제공한다. [초안](canvas-drafts.md)·[본문 CAS](canvas-document-save.md)·[태그](canvas-tags.md)·[이미지 참조](canvas-assets.md)를 조합하며, 구현·검증·ready PR·main 병합 상태는 [worklog0294](../../worklog/0294-canvas-publication.md)와 이슈/PR에서 구분한다.

## 편집 상태와 공개 상태

`Canvas.status=draft/trashed`는 편집·휴지통 수명주기다. `draft`인 Canvas에도 현재 공개본이 있을 수 있다. 작성자 응답의 `view=draft`와 `canvas.status=draft`를 미게시 여부로 해석하지 않는다. `publication` 요약의 존재가 현재 게시 여부이며 `publication_revision`은 공개 상태의 지속 CAS token이다. 공개 응답은 별도 DTO의 `view=publication`, `canvas.status=published`로 구분한다. 내부 Canvas의 status를 published로 바꾸지 않는다.

| 작업 | 편집 metadata/document revision | publication_revision | 공개본 |
| --- | --- | --- | --- |
| 생성 | 각각0 | 0 | 없음 |
| metadata PATCH / 본문 PUT | 해당 초안 clock만 증가 | 유지 | 마지막 snapshot 유지 |
| 최초 게시 / 변경한 source 재게시 | 유지 | +1 | 현재 source로 생성·교체 |
| 동일 source 재게시 | 유지 | 유지 | 같은 snapshot·게시 시각 유지 |
| 게시 취소 | 유지 | 공개본이 있으면 +1 | snapshot·publication 참조 제거 |
| 휴지통 | metadata만 +1 | 공개본 제거 시 +1 | 제거, draft 참조/본문은 보존 |
| 휴지통 복구 | metadata만 +1 | 유지 | 자동 재게시 없음 |

취소 뒤에도 counter가 남는다. 예를 들어 게시1→취소2→재게시3이며, 예전 `expected_publication_revision=1`의 게시·취소 요청은 모두409다. 실제 상태 전이마다 token을 바꿔 취소 이전 요청이 다시 살아나는 ABA 경쟁을 막는다. 초안 clock과 공개 clock은 독립적이다.

## API와 revision

경로는 `/api/v1` 기준이다. 새 POST는 현재 active 계정의 Bearer 세션 전용이며 API Key는401이다. 모든 성공 응답은 `Cache-Control: private, no-store`다.

```json
{
  "expected_metadata_revision": 2,
  "expected_document_revision": 5,
  "expected_publication_revision": 0
}
```

`POST /canvases/{id}/publish`는 위 세 필드를 필수로 받는다. 현재 작성자·active 멤버·active Board·현재 Shelf의 read_canvas/create_canvas를 검사한 뒤 metadata→document→publication의 기대 revision을 검사한다. 본문을 같은 `CanvasContent`로 다시 검증하고 같은 Board/Canvas의 ready 이미지만 publication 참조에 연결한다. 제목/요약/visibility·태그 ID/최초 표시명/순서·본문·source metadata/document revision·게시 시각을 원자 저장한다. 이미 같은 source revision의 공개본이 있어도 stale 기대값을 먼저 거부한다. source revision이 바뀌었으면 내용이 같아도 새 provenance의 게시로 취급한다.

`POST /canvases/{id}/unpublish`는 `{ "expected_publication_revision": 1 }`만 받는다. 현재 작성자·계정·active 멤버·active Board를 요구하며, 작성 등급이나 Shelf 읽기 권한이 낮아져도 자신의 공개본을 철회할 수 있다. 운영자에게 타인 공개본 철회 권한을 주지 않는다. 현재 token이 맞는 미게시 draft는200 no-op이다. 휴지통은409, 보관 Board 변경은403, 제재·정지·타인/없는 객체는404다.

두 POST의200 응답은 `metadata_revision`, `document_revision`, 현재 `publication_revision`, `publication`을 반환한다. 공개본이 있으면 publication에는 `publication_revision/source_metadata_revision/source_document_revision/published_at`을, 없으면 null을 담는다. 최상위 clock은 현재 초안/상태 clock이며 publication 안의 source clock은 게시 당시 값이다.

기대 revision은 엄격한 JSON 정수0~2^63-1이다. 문자열/소수/bool/null·추가 필드는422다. metadata/document/publication 충돌은 각각 `CANVAS_REVISION_CONFLICT`, `CANVAS_DOCUMENT_REVISION_CONFLICT`, `CANVAS_PUBLICATION_REVISION_CONFLICT`409와 `details.current_revision`을 반환한다. publication clock 상한에서는 실제 상태 변경을409로 거부하고 전체 rollback하며 동일 source/state no-op은 허용한다. 유효하지 않은 저장 본문은 `CANVAS_DOCUMENT_INVALID`409, 잘못된 이미지 참조는 `ASSET_INVALID_REFERENCE`422다. DB 실패는 `CANVAS_UNAVAILABLE`503이다.

## GET view와 공개 whitelist

metadata·document·asset GET은 optional Bearer다. 토큰이 없으면 익명이며, API Key-only도 익명으로 취급해 멤버·작성자 권한을 대신하지 않는다. invalid Bearer는401, 비활성/삭제 계정 토큰은 기존404이며 익명으로 강등하지 않는다. OpenAPI security에는 Bearer와 익명 대안을 함께 선언한다.

| view | 현재 작성자 | 나머지 요청자 |
| --- | --- | --- |
| 생략 | 기존 작성자 전용 draft | 현재 publication |
| draft | 기존 작성자 전용 draft | 404 |
| publication | 현재 공개 읽기 정책 적용 | 같은 현재 공개 읽기 정책 적용 |

`GET /canvases/{id}`의 draft 응답에는 기존 canvas/document_revision/capabilities에 현재 publication token/요약을 더한다. `capabilities.publish`는 현재 작성 가능 여부, `unpublish`는 현재 철회 가능 여부다. 편집 중인 제목·태그는 계속 draft 응답에만 반영한다.

공개 응답의 canvas는 `id/board_id/shelf_id/author_id/title/summary/visibility/status/tags`만 담는다. 제목/요약/visibility/태그는 snapshot에서, Board/Shelf 소속과 author_id는 현재 Canvas에서 읽는다. publication source revision/시각은 최상위 필드로 명시한다. 초안 revision·변경 시각·휴지통 필드·사용 건수·이메일·계정 이름·스토리지 키를 섞지 않는다. 공개 capabilities는 read_document만 true다.

`GET /canvases/{id}/document`의 publication 응답은 typed document와 `revision=source_document_revision`, view 및 publication 요약을 반환한다. 현재 초안 document revision은 공개 응답에 포함하지 않는다. 썸네일/preview_status/생성 작업은 없으며 소비자는 기본 미리보기를 사용한다.

## 현재 권한과 공개 범위

매 요청마다 현재 Board visibility/status, 해당 요청자의 가입/제재·등급, 현재 Shelf read_canvas를 기존 BoardPermissionService로 평가한다. private Board는 active 멤버만, suspended Board와 suspended/banned 멤버는404다. pending/탈퇴/비회원은 public 읽기 조건만 사용할 수 있다. archived Board는 공개본 읽기를 허용하고 변경을 거부한다. staff_bypass는 기존 Shelf 정책 범위이며 타인 draft 접근은 허용하지 않는다.

Canvas의 현재 visibility와 snapshot.visibility 중 하나라도 members이면 active 멤버를 요구한다. 따라서 public→members 축소는 즉시 적용되고, members→public 확대는 새 snapshot을 게시해야 적용된다. 같은 Board Shelf 이동도 현재 목적지 읽기 정책을 즉시 적용하며 공개 내용은 유지한다. Board 자체의 private/public 전환은 기존 Owner 정책에 따라 현재 경계를 즉시 바꾼다.

PostgreSQL 공개 단건 읽기는 Board 공유 잠금→인증된 active User 공유 잠금→Canvas 공유 잠금 아래 현재 정책과 snapshot/태그/이미지 참조를 일관되게 읽는다. SQLite는 명시적 읽기 transaction을 사용한다. 이미 권한을 확보한 진행 중 요청은 snapshot을 마칠 수 있으며 전달된 정보의 회수는 보장하지 않는다. 이미지 파일 stat/get은 DB transaction이 닫힌 후 실행한다.

## 이미지·삭제·저장 책임

이미지 GET은 같은 view/공개 가드와 **현재 publication scope 참조**가 있는 ready Asset만 반환한다. draft-only·미참조·교체된 이전 공개본의 ID는404다. 작성자의 기본 draft view는 기존 미참조 ready 이미지 읽기를 유지한다. 공개 이미지도 private/no-store·nosniff·UUID 파일명과 기존 저장소 위치/크기/MIME/해시 검사를 사용한다.

게시/교체·취소·휴지통은 같은 세션의 `AssetTransaction.replace_refs(scope="publication")`를 사용한다. draft scope를 건드리지 않고 마지막 참조 해제 시 기존24시간 유예/outbox를 복구한다. 다른 초안/공개본/Board/프로필 참조 보호·lease fencing·재시도와 파일 I/O 경계는 유지한다. Board 영구 삭제는 publication/counter/tag를 Canvas FK CASCADE로 정리하고 기존 파일 outbox는 부모 삭제 후에도 보존한다. 계정 삭제는 현재 author_id/asset owner_id만 SET NULL로 익명화하며 이미 게시된 snapshot은 현재 읽기 정책 아래 남는다. 복구는 draft만 복원한다.

SQL·세션·ORM 쓰기·트랜잭션·DB 오류 변환은 `models/canvas.py`와 조합한 기존 모델이 소유한다. 서비스는 현재 정책/DI/흐름만 담당한다. 변경 잠금 순서는 Board→active User 공유→Canvas→Document→정렬한 해당 Canvas Asset→outbox이며 파일 I/O는 밖에서 수행한다. flush/commit 실패는 counter·snapshot·태그·참조·TTL/outbox를 함께 rollback한다. commit 응답만 유실되면 실제 게시가 완료됐을 수 있으므로 GET으로 재확인하고 파일을 보상 삭제하지 않는다.

## 0029 migration과 검증

`0029_canvas_publications`는 새 테이블만 생성한다. Canvas 부모 CHECK·FK·상태는 그대로여서 SQLite batch 재생성/자식 CASCADE 손실을 피한다.

- `canvas_publication_counters`: Canvas PK/FK CASCADE와 지속 BIGINT revision.
- `canvas_publications`: Canvas PK/FK CASCADE, 현재 snapshot/source clocks·공개 필드/JSONB/게시 시각. `(published_at,canvas_id)` 인덱스.
- `canvas_publication_tags`: `(canvas_id,tag_id)` PK, publication CASCADE·Tag RESTRICT, 최초 표시명/0~9 순서와 `(canvas_id,position)` UNIQUE, `(tag_id,canvas_id)` 조회 인덱스. [공개 목록 필터](canvas-feed.md)는 mutable canvas_tags 대신 이 snapshot 연결을 사용한다.

기존 Document/Asset/ref/Tag/outbox를 가진 FK 활성 SQLite와 실제 PostgreSQL에서 이전0028→head 데이터 보존을 검증한다. counter/history 또는 publication 참조가 남은 downgrade는 거부해 CAS 이력과 파일 보호를 잃지 않는다. 데이터가 없는 새 테이블의 downgrade/upgrade는 기존 콘텐츠를 보존한다. 운영 사고 대응은 기존 rollforward-first를 따른다.

API/SQLite 검사는 공개본 불변·현재 권한/view/API Key·이미지·CAS/overflow·휴지통/SET NULL/Board 삭제·flush/commit/불확실한 commit을 확인한다. opt-in 실제 PostgreSQL 검사는 고유 임시 schema에서 migration·JSONB·게시/취소/저장/metadata 경쟁, 현재 권한 회수의 lock wait, 공개 읽기의 공유 잠금 양방향, 취소/cleanup 양방향과 계정 삭제 경쟁을 확인하고 schema 제거를 재검증한다. 기본 전체 검사에서 opt-in은 skip되므로 별도 실행 결과를 worklog에 기록한다.

[목록/Plaza·cursor/필터 #53](canvas-feed.md)은 별도 백엔드 계약이다. [공식 홈 #55](board-home-layout.md)의 collection도 공개 header/고정 Tag와 현재 권한만 사용하고 작성자/Owner의 미게시 초안은 섞지 않는다. 개인 draft 목록·운영자 moderation·Canvas archive/자동 purge·썸네일 생성·신규 UI/운영 배포는 이 단위에 포함하지 않는다. #51 완료가 상위 #8/#6/#7/#24 전체 완료를 의미하지 않는다.
