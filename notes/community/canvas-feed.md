# 공개 Canvas 목록·커서·필터 — #53 / #8

게시된 snapshot을 Plaza·Board·Shelf에서 조회한다. [게시·단건 열람](canvas-publication.md)의 현재 권한과 [공식 Interest·자유 Tag](canvas-tags.md)의 구분을 유지한다. 로그인한 방문자는 자신이 현재 읽을 수 있는 members/private 게시본도 볼 수 있다. 작성자에게도 이 목록은 공개본만 반환한다. 구현·검증·ready PR·main 병합은 [worklog0295](../../worklog/0295-canvas-feed.md)와 [#53](https://github.com/Blueprint4Agent/Canvanity/issues/53)에서 구분한다.

## 경로와 입력

모든 경로는 `/api/v1` 기준이다.

| GET | 범위·추가 필터 |
| --- | --- |
| `/canvases` | Plaza. optional `board_id`·`shelf_id` UUID를 AND로 적용한다. |
| `/boards/{board_id}/canvases` | 현재 Board의 게시본. 소속 query 재지정은 허용하지 않는다. |
| `/shelves/{shelf_id}/canvases` | 현재 Shelf의 게시본. 소속 query 재지정은 허용하지 않는다. |

| 공통 query | 계약 |
| --- | --- |
| `limit` | 정수1~100, 기본20. |
| `sort` | `latest`만 허용, 기본 `latest`. |
| `interest_id` | 활성 공식 Interest의 slug. 소문자/숫자/kebab-case, 2~40자. 현재 Board 연결에서 조회한다. |
| `tag_id` | UUID 하나. 게시 당시 `canvas_publication_tags` 연결에서 조회한다. |
| `cursor` | 다음 페이지의 Base64URL 문자열. 1~2048자. |

Interest와 Tag는 독립적인 AND 조건이다. 문법이 유효하지만 없는/비활성 Interest·없는 Tag는200 빈 결과다. 자유 Tag를 Shelf나 공식 Interest로 간주하지 않으며, 초안 `canvas_tags` 변경은 재게시 전 결과와 공개 태그를 바꾸지 않는다. 공식 User 최대8·Board 최대3 정책은 그대로다. 지원하지 않는 query(`q`, 인기순 등)·잘못된 UUID/형식/한도는422다.

Board 범위와 전역 `board_id`는 같은 Board 존재·현재 읽기 경계를 적용한다. Board를 읽을 수 있지만 허용 Shelf/게시본이 없으면200 빈 목록이다. Shelf 범위와 전역 `shelf_id`는 Board와 해당 Shelf의 현재 `read_canvas` 정책을 요구한다. 없는/읽을 수 없는 scope와 다른 Board/Shelf 조합은 같은 `CANVAS_NOT_FOUND`404다. Interest/Tag가 빈 결과를 만들더라도 읽을 수 없는 scope를200으로 바꾸지 않는다. `is_visible=false`는 메뉴 표시 설정이며 직접 Shelf 범위/게시본 열람을 막지 않는다.

## 응답과 수명주기

응답은 `{items,next_cursor}`이며 `total`은 없다. 항목마다 다음 공개 필드만 제공한다.

```json
{
  "canvas": {
    "id": "00000000-0000-4000-8000-000000000001",
    "board_id": "00000000-0000-4000-8000-000000000002",
    "shelf_id": "00000000-0000-4000-8000-000000000003",
    "author_id": null,
    "title": "공개한 제목",
    "summary": "공개 요약",
    "visibility": "public",
    "status": "published",
    "tags": []
  },
  "board": {"id": "00000000-0000-4000-8000-000000000002", "slug": "example", "name": "예시 보드"},
  "shelf": {"id": "00000000-0000-4000-8000-000000000003", "slug": "general", "name": "자유"},
  "publication_revision": 1,
  "source_metadata_revision": 2,
  "source_document_revision": 3,
  "published_at": "2026-11-03T11:00:00.123456Z",
  "view": "publication"
}
```

title/summary/visibility/정렬 tags/source clocks/게시시각은 snapshot 값이다. Canvas의 board_id/shelf_id/author_id와 Board/Shelf의 id·slug·name은 현재 관계다. 계정 삭제 뒤 author_id는 SET NULL로 유지한다. 본문 JSONB·초안 revision/변경시각·이메일/계정 이름·스토리지 키·사용 건수·편집 capabilities는 읽거나 노출하지 않는다. 항목의 `status=published`는 공개 DTO이며 DB 편집 상태를 바꾸지 않는다.

최신순은 `published_at DESC, canvas_id DESC`다. 초안 metadata/본문 저장은 순서를 바꾸지 않고, 변경한 source의 재게시·새 게시는 새 게시시각 위치에 나타난다. 같은 source/state의 publish no-op은 시각을 유지한다. 게시 취소·휴지통은 목록에서 제거되고 복구가 자동 게시하지 않는다. Shelf 이동은 현재 소속/목적지 정책을 다음 읽기에 적용하며 공개 내용은 다음 재게시 전까지 유지한다.

## 현재 권한·인증

매 요청에서 현재 활성 계정·Board 상태/visibility·멤버 상태/역할/등급·Shelf override 또는 Board 기본 `read_canvas`를 검사한다. `BoardPermissionService`와 SQL의 운영 역할 상수는 공유하며 SQLite/실제 PostgreSQL에서 단건 `view=publication`과 허용/거부를 대조한다.

- suspended Board와 suspended/banned 멤버는 제외한다. archived Board의 읽기는 허용한다.
- private Board는 active 멤버만 읽는다. pending/탈퇴/비회원은 public 조건만 사용할 수 있다.
- 현재 Canvas visibility 또는 snapshot.visibility 중 하나라도 members면 active 멤버를 요구한다. members→public 확대는 재게시가 필요하다.
- staff_only/staff_bypass와 같은 Board의 현재 등급 rank를 적용한다. 앱 전역 Admin과 API Key는 Board 운영 역할이나 멤버 자격을 대신하지 않는다.

optional Bearer를 사용한다. 토큰 없음/API Key-only는 익명이고 invalid Bearer는401 `INVALID_TOKEN`, 비활성/삭제 계정은 기존404 `USER_NOT_FOUND`이며 익명으로 강등하지 않는다. 성공 응답은 `Cache-Control: private, no-store`다. OpenAPI는 Bearer와 익명 대안을 함께 선언한다. DB 실패는503 `CANVAS_UNAVAILABLE`이다.

## 커서와 동시 변경

허용된 행에 필터/정렬을 적용한 뒤 `limit+1`을 조회한다. 다음 커서는 마지막 **반환** 항목에서만 만들고 추가 확인 행이나 제한 행의 ID를 넣지 않는다. 서비스에서 후보를 먼저 limit한 뒤 권한으로 제거하지 않는다.

커서는 `v=1`, `domain=canvas-publication-feed`, 경로별 scope(`plaza`, `board:UUID`, `shelf:UUID`), `sort=latest`, 소속·Interest·Tag의 canonical SHA-256 `filter_hash`, 마지막 UTC RFC3339 `published_at`, UUID `canvas_id`만 받는다. 정수/bool 혼동·날짜/시간대·UUID·추가/중복 JSON key·잘못된/비정규 Base64URL·길이를 검사한다. scope/필터가 다른 커서와 잘못된 payload는422 `CANVAS_INVALID_CURSOR`다. limit만 바꾸는 것은 허용한다. 서명 없는 커서는 권한 증명이 아니며 사용자 간 전달해도 각 요청자의 현재 권한을 다시 적용한다.

PostgreSQL의 단일 SELECT statement MVCC에서 계정/scope 허용 여부, readable Board/Shelf·현재 정책, publication header page CTE와 ordered publication tags LEFT JOIN을 함께 읽는다. SQLite도 한 SELECT로 읽는다. 여러 Board를 항목별로 조회하지 않으며 태그 JOIN 전에 페이지를 결정한다. 별도 header/tag 쿼리 사이 재게시가 끼어 이전 제목과 새 태그가 섞이는 경로가 없다. 읽기 시작 뒤 완료된 권한 변경은 다음 요청에서 반영되며 이미 시작한 응답의 회수를 보장하지 않는다.

여러 페이지 요청 사이 새 게시·재게시·취소·이동·권한 변경은 가능하다. 이 keyset은 전체 기간을 고정한 snapshot pagination이나 정확한 전체 건수를 보장하지 않는다. 필터/범위를 바꾸면 첫 페이지부터 다시 조회한다.

## 저장소와 검증·후속

`routers/v1/canvas.py → CanvasFeedService → models/canvas_feed.py`의 모델 저장소가 SQL·세션·DB 오류 변환을 소유한다. 서비스는 DI·커서·scope 결과 흐름만 담당한다. 기존 게시 정렬 `(published_at,canvas_id)`, 게시태그 `(tag_id,canvas_id)`, Board/Shelf·회원/등급·정책/관심사 키를 사용하며 새 migration은 없다. 결과 limit는 대형 권한 JOIN/scan 비용의 상한이나 처리량 SLA가 아니다. JSONB GIN·인기순/추천 인덱스는 선행 추가하지 않는다.

API/SQLite 검사는 query/응답 whitelist·실제 Bearer/API Key·권한 행렬·동일시각 UUID tie·다중 태그·필터/초안 비노출·페이지 사이 제재·게시/재게시/취소/이동/휴지통/SET NULL과 단건 parity를 검증한다. opt-in 실제 PostgreSQL은 localhost의 고유 임시 schema에서 같은 시나리오와 단일 statement 결과 뒤 재게시/권한 축소가 완료되는 경쟁·EXPLAIN·기존 인덱스를 확인하고 schema 제거를 재검증한다. 기존 개발 DB/파일을 수정하지 않는다. 기본 전체 검사에서 opt-in skip과 별도 PostgreSQL 실행을 구분해 기록한다.

Board 홈 동적 widget/공식 layout 백엔드는 [#55 계약](board-home-layout.md)으로 연결한다. 공개 header/정렬 Tag와 현재 읽기 SQL을 공유하며 홈 전체 snapshot 안에서 source를 중복 제거해 한 ranked query로 읽는다. 새 UI·공식 홈 제품 편집/개인 배치 #25·개인 draft 목록 UI·썸네일 생성·추천/인기순·운영자 moderation·Canvas archive/자동 purge·댓글/좋아요/구독 #26·운영 배포는 후속이다. #53 완료는 상위 #8/#24 전체 UI 완료를 의미하지 않는다.

## 내 Canvas 목록·휴지통 #57

[세션 전용 내 목록](canvas-list.md)은 현재 active 계정·Board active/archived·active 멤버인 본인의 기존 Board 소속 행만 조회한다. 낮은 Shelf 등급도 본인 초안 읽기를 막지 않고 단건과 같은 capabilities/30일 복구 기한을 적용한다. metadata/본문 최근 수정순과 독립 status/publication 필터를 사용하며 공개 snapshot 목록·단건 공개본 읽기 경계를 넓히지 않는다. 제품 UI는 후속이다.
