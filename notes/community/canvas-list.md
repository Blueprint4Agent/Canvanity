# 내 Canvas 목록·휴지통 — #57

`GET /api/v1/me/canvases`는 기존 Board 소속 **본인** 초안과 휴지통의 조회 API다. 프로필 My Canvas UI와 독립 개인 문서를 새로 만들지 않는다. 구현·검증·ready PR·main 병합은 worklog/0297-my-canvas-list.md 및 [#57](https://github.com/Blueprint4Agent/Canvanity/issues/57)의 실제 상태로 구분한다. 상위 #8의 제품 UI/수직 흐름은 후속이다.

## 인증·범위

현재 활성 계정의 Bearer 세션이 필요하다. API Key-only와 잘못된 Bearer는401 `INVALID_TOKEN`, 조회 snapshot에서 비활성/삭제 계정은404 `USER_NOT_FOUND`다. `author_id`/`user_id` 같은 임의 작성자 선택 및 미지원 query는422다. 성공 응답은 `Cache-Control: private, no-store`다.

현재 `active` 멤버이고 Board가 `active` 또는 `archived`인 본인 행만 조회한다. private Board도 본인이 active 멤버이면 허용한다. pending/탈퇴/정지/차단·suspended Board는 제외하고, 앱 전역 관리자/Board 운영자도 타인의 초안을 조회하지 못한다. 허용 행을 먼저 판정한 뒤 keyset과 limit를 적용한다. 낮은 Shelf 읽기 등급은 본인 단건 초안과 마찬가지로 목록을 숨기지 않으며, 현재 편집/복구 권한은 별도로 계산한다.

`board_id`/`shelf_id`는 선택적 UUID이며 함께 주면 같은 Board의 Shelf여야 한다. 없는/미허용/서로 다른 Board의 scope는 동일404 `CANVAS_NOT_FOUND`다. Shelf scope는 현재 read_canvas가 허용되거나 그 Shelf에 본인 Canvas가 실제로 있어야 한다. 이 본인 존재 검사는 status/publication/cursor와 독립적이다. 읽기 제한 Shelf에 본인 글도 없으면 존재를 구별하지 못하도록 없는/타 Board scope와 같은404이며, 읽기 허용 빈 Shelf 또는 본인 글이 있는 Shelf에서 선택 필터와 맞는 행이 없으면200 빈 목록이다. 숨긴 Shelf 메뉴도 작성자 scope에서는 조회할 수 있다. 관계의 이름·slug·등급/정책은 반환하지 않고 기존 본인 metadata의 board_id/shelf_id만 유지한다.

## 필터·응답

| Query | 기본값 | 허용값/의미 |
| --- | --- | --- |
| status | draft | draft / trashed / all: 편집 lifecycle |
| publication | all | all / published / unpublished: 현재 publication 존재 |
| board_id, shelf_id | 생략 | 현재 본인 읽기 scope의 선택 범위 |
| sort | last_modified | 메타데이터/본문 중 최근 수정 시각 내림차순 |
| limit | 20 | 1~100 |
| cursor | 생략 | 최대2048자, 같은 사용자·필터·정렬의 다음 페이지 |

모든 필터는 AND다. `status=draft`에도 게시된 Canvas가 포함된다. publication은 status와 독립된 축이며 게시/취소는 편집 상태 enum을 바꾸지 않는다. 정상 휴지통 이동은 publication을 제거하므로 `status=trashed&publication=published`는 빈 목록이다.

응답은 `{items,as_of,next_cursor}`다. 각 항목은 작성자 단건 `CanvasResponse`의 canvas(현재 title/summary/visibility/status/revision·정렬한 현재 draft Tags·생성/metadata 수정/휴지통 시각), document_revision, view=draft, publication_revision(취소 이후에도 남는 상태 token), publication(현재 공개본 revision/source clocks/published_at 또는 null), capabilities를 재사용한다. 공개 목록과 달리 본인 현재 draft metadata/Tags이며 공개 snapshot 제목/태그가 아니다.

목록 전용 필드는 `document_updated_at`, `last_modified_at`, `trash_expires_at`, `trash_expired`다. 일반/게시 본문 JSONB·Asset/URL·관계 이름·total은 읽거나 반환하지 않는다. 일관 snapshot에서 필요한 Document가 없으면 단건과 같은503 `CANVAS_UNAVAILABLE`이며 조용히 행을 누락하지 않는다. DB 실패도 같은 도메인503으로 변환한다.

## 권한·복구 기한

단건과 목록은 같은 순수 capability helper를 사용한다. draft의 edit_metadata/edit_document/publish는 현재 Shelf의 read_canvas와 create_canvas를 모두 요구한다. active Board에서 본인 draft의 trash와 현재 공개본 unpublish는 낮은 등급이어도 가능하다. archived Board는 읽기만 허용한다. restore는 trashed·현재 작성 권한·미만료를 모두 요구한다.

`trash_expires_at = trashed_at + 30일`이며 정확히 기한과 같거나 지났으면 `trash_expired=true`, `restore=false`다. 미휴지통 항목은 기한=null/만료=false다. 만료된 행을 자동 삭제하지 않고 계속 조회할 수 있다. `as_of`는 응답 전체의 복구 기한/capabilities 평가에 한 번 캡처한 UTC 시각이다. DB의 역사 조회 cutoff나 정확한 snapshot 생성 시각을 나타내지는 않는다. 단건 조회는 각 요청 시각에 다시 판단하므로 기한을 가로지르는 별도 요청은 결과가 달라질 수 있다.

## 정렬·커서·동시 변경

`last_modified_at=max(Canvas.updated_at, CanvasDocument.updated_at)`를 사용하고 같은 시각은 Canvas UUID 내림차순이다. 기존 metadata/document 수정 시각과 revision을 새로 쓰거나 통합하지 않는다. 본문 저장도 최근 수정순에 반영한다. 게시/재게시/게시 취소 자체는 이 두 편집 clock을 바꾸지 않아 순서가 유지될 수 있다. 실제 metadata 변경·Shelf 이동·휴지통/복원은 기존 metadata clock 동작을 따른다.

허용 행을 `limit+1`로 조회하며 다음 커서는 마지막 **반환** 항목으로 만든다. 최대100개 응답에 추가 확인 행1개를 읽을 수 있다. cursor는 `v=1`, `domain=canvas-owner-list`, 현재 `user_id`, `sort=last_modified`, 정규 status/publication/board_id/shelf_id의 SHA-256 filter_hash, UTC RFC3339 last_modified_at, UUID canvas_id를 갖는다. 정수/bool 혼동·추가/중복 JSON key·잘못된 날짜/시간대·UUID·비정규 Base64URL·길이를 엄격히 검사한다. 다른 사용자/필터/공개 목록 domain 또는 잘못된 cursor는422 `CANVAS_INVALID_CURSOR`다. limit만 바꾸는 것은 허용한다. 서명 없는 cursor를 권한 증명으로 사용하지 않고 SQL에서 현재 author와 멤버 자격을 다시 고정한다.

페이지 요청 사이 편집/본문 저장·이동·게시 상태·휴지통·정책/멤버 변경은 가능하다. 이미 커서 앞쪽으로 수정된 항목은 다음 페이지에서 건너뛸 수 있고, 현재 필터/권한에서 빠진 항목은 제외한다. 전체 기간을 고정한 snapshot pagination/정확한 건수는 보장하지 않는다. 목록을 갱신하거나 필터를 바꾸면 첫 페이지부터 다시 조회한다.

## 저장소·검증·보류

`canvas router → CanvasListService → models/canvas_list.py`에서 모델 저장소가 SQL·세션·DB 오류 변환을 소유한다. PG `REPEATABLE READ READ ONLY`/SQLite `BEGIN` snapshot 안에서 계정/scope, 현재 작성자 header와 Board/member, grade·Board/Shelf 정책·현재 Tags를 최대6개 SELECT의 batch로 읽는다. Shelf scope는 Board/member와 필터 독립 본인 존재를1회 더 조회하고 같은 정책 batch로 현재 read 허용 여부를 판단하므로 최대7개 SELECT다. 행이 없거나 scope가 막히면 더 적게 읽는다. 서비스는 기존 BoardPermissionService와 공유 capability helper로 판정하며 항목별 SQL/단건 서비스 호출을 하지 않는다. snapshot 시작 뒤 완료된 권한 변경은 다음 요청에 반영하며 이미 시작한 응답의 회수를 보장하지 않는다.

기존 author_id·Board/Shelf·정책·Tag 키를 재사용하며 새 migration/startup 변경은 없다. 계산 시각 정렬은 별도 표현식 인덱스를 선행 추가하지 않는다. 격리 PG EXPLAIN과 작은 fixture는 쿼리 구조/기존 키의 근거이며 큰 목록 처리량이나 scan/sort 입력의 상한을 보장하지 않는다.

API/SQLite와 opt-in localhost PostgreSQL 고유 schema에서 필터·동일시각 페이지·현재 계정/Board/회원/등급/재정의 정책·단건 capabilities parity·정확한30일 경계·전환·누락 Document/DB 실패·본문 미SELECT·고정 조회 수·기존 테이블 보존을 확인한다. PG는 header 읽기와 정책/Tag batch 사이 별도 트랜잭션의 metadata/document clock·게시 counter·Tag·정책/제재 변경에도 이전 snapshot이 일관되는지 검사하고 schema 정리를 확인한다. 원본 개발 DB/env/파일은 보존한다.

목록 UI·독립 개인 문서·썸네일·자동 purge/영구삭제·moderation/archive·다중 Board 공유·댓글/좋아요/구독·운영 배포는 후속이다. 기존 [초안](canvas-drafts.md), [게시](canvas-publication.md), [공개 목록](canvas-feed.md) 계약을 유지한다.
