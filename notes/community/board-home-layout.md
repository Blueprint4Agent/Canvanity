# Board 공식 홈 레이아웃 — #55 / #25

운영자가 저장하는 UI Canvas 문서와 방문자의 현재 권한으로 계산하는 위젯 데이터를 분리한다. [#55](https://github.com/Blueprint4Agent/Canvanity/issues/55)는 백엔드 단위이며 구현·검증·ready PR·main 병합은 [worklog0296](../../worklog/0296-board-home-layout.md)와 이슈/PR에서 구분한다. 제품 편집 UI·개인 배치·Plaza/Profile 배치·공동 편집은 후속이며 미디어 업로드는 [#59](board-media.md) 계약을 따른다.

## 관리 API와 권한

`GET /api/v1/boards/{board_id}/layout`은 `{board_id,document,layout_revision}`을 반환한다. `PUT`은 다음 전체 문서와 `expected_revision`, 필수 감사 `reason`(공백 제거 후 1~500자)을 받고 같은 형태를 반환한다. 두 경로는 Bearer 세션, 현재 활성 계정과 해당 Board의 active Owner/Admin을 요구한다. Moderator·Curator 등 활동 등급·다른 Board 운영 역할·앱 전역 admin·API Key는 관리 권한을 추가하지 않는다. Board suspended/제재 멤버는 404, 일반 역할은 403이다. archived는 관리 GET만 허용하고 PUT은 403이다. 성공 응답은 `Cache-Control: private, no-store`다.

```json
{
    "expected_revision": 0,
    "reason": "공식 홈 최신 글 배치",
    "document": {
        "schema_version": 1,
        "widgets": [
            {
                "id": "latest",
                "type": "canvas_collection",
                "position": { "x": 850, "y": 100 },
                "size": { "width": 850, "height": 650 },
                "source": {
                    "board_id": "00000000-0000-4000-8000-000000000001",
                    "shelf_id": null,
                    "sort": "latest",
                    "limit": 6
                }
            }
        ]
    }
}
```

## UI 문서 스키마

루트는 `schema_version=1`, `widgets`만 허용한다. Content Canvas의 engine/settings/nodes/edges/element_order·카메라·선택·개인 상태는 거부한다. 중첩 모델 모두 추가 필드를 거부하며 SQL/JS/외부 HTML/URL·다른 Board·임의 Asset ID는 실행하거나 참조하지 않는다.

| 필드 | 계약 |
| --- | --- |
| ID | ASCII 영숫자로 시작하는 영숫자/밑줄/하이픈 1~80자, 문서 안에서 유일. |
| position | x/y는 JSON number인 유한수, 각 축 -100,000~100,000. 문자열/bool 변환 없음. |
| size | width/height는 유한 JSON number, 각 축 0 초과~100,000. |
| widgets | 0~100개. 배열 순서가 공식 순서다. |
| 문서 크기 | 정규 UTF-8 JSON 256KiB 이하. 키 정렬·공백 제거·null 생략으로 계산한다. |
| 요청 크기 | JSON 파싱 전 스트림 256KiB+4KiB. 초과는 413 `BOARD_LAYOUT_TOO_LARGE`; 스키마/문서 한도는 422. |

| type | source/config | 현재 widget_data |
| --- | --- | --- |
| board_intro | 별도 source 없음. | 현재 Board 허용 요약과 rules. |
| board_cover | 별도 source/asset_id/URL 없음. | 같은 snapshot의 현재 Board cover 요약 또는 `null`. [미디어 계약](board-media.md). |
| shelf_navigation | 별도 source 없음. | 읽기 허용 및 is_visible인 Shelf 요약/액션만. |
| canvas_collection | 현재 Board UUID, 선택 shelf_id, sort=latest, limit 1~20(기본 6). | 게시 snapshot header/고정 Tag만, items 최대 limit개. |

collection의 board_id는 필수다. shelf_id는 생략/null이면 Board 전체, UUID이면 현재 Board에 실존하는 Shelf를 지정한다. 숨김 Shelf도 읽기 정책이 허용하면 직접 source로 사용할 수 있다. PUT의 타 Board/외부/없는 Shelf는 422 `BOARD_INVALID_LAYOUT_SOURCE`다. 기존 Board 생성의 3개 기본 위젯 문서는 그대로 검증/조회된다. 관리 GET 문서를 그대로 PUT할 수 있다.

## 독립 revision과 최소 감사

기존 `board_layouts.revision INTEGER`를 유지하고 API도 엄격 정수 0~2,147,483,647로 제한한다. 이번 변경에는 migration/타임스탬프 컬럼을 추가하지 않는다. 이전 도메인 표의 BIGINT/updated_at은 실제 구현이 아니었으며 현재 표를 정정했다.

PUT은 Board FOR UPDATE → 활성 User FOR SHARE → 현재 멤버 역할 → layout FOR UPDATE 순서로 확인한다. 다른 역할/정책 변경도 Board 잠금을 사용하므로 대기 중 권한을 회수하면 저장은 거부된다. SQLite 쓰기는 BEGIN IMMEDIATE로 직렬화한다. stale를 먼저 409 `BOARD_LAYOUT_REVISION_CONFLICT`와 `current_revision`으로 거부한다. 이후 동일 정규 문서는 200 no-op이며 revision·감사·Board revision 모두 유지한다. 실제 변경은 layout revision만 1 증가한다. 상한의 no-op은 허용하고 상한에서 문서를 변경하면 409 `BOARD_LAYOUT_REVISION_EXHAUSTED`다.

문서/새 revision과 기존 board_member_audit의 `layout_updated`를 한 트랜잭션에 저장한다. 감사에는 actor, reason, before_revision/after_revision, canonical SHA256 before_hash/after_hash, widget_count만 넣고 문서/본문/위젯 설정은 복제하지 않는다. 기존 member-audit 응답의 `layout_change`로 같은 허용 필드를 제공한다. 저장 실패는 503 `BOARD_UNAVAILABLE`로 변환하고 열린 트랜잭션의 문서/revision/감사를 함께 롤백한다. commit 결과가 불명확한 연결 장애에서는 관리 GET으로 현재 revision을 확인한 뒤 재시도한다. Board 삭제 시 layout/감사는 기존 CASCADE를 따른다.

## 방문자 홈과 비노출

기존 `GET /boards/{id}/home`, `GET /boards/{id}`, `GET /boards/by-slug/{slug}`는 기존 board/rules/membership/grades/shelves/layout/layout_revision을 유지하며 `widget_data`를 더한다. layout은 엄격 스키마를 통과한 방문자용 projection이고, widget_data는 같은 ID/type에 대응하는 현재 결과다. 결과를 저장 문서에 캐시하지 않는다.

Shelf source를 읽을 수 없거나 저장 후 해당 빈 Shelf가 삭제됐으면 그 위젯 전체를 layout과 widget_data 양쪽에서 생략한다. custom ID·Shelf ID·이름·source/config·게시 제목/요약·태그·본문·개수를 placeholder로 노출하지 않는다. 관리 GET은 수정에 필요한 기존 전체 설정을 유지한다. 삭제된 source를 포함한 새 PUT은 거부되므로 편집자는 이를 제거/대체해 복구한다. 전체 Board collection은 현재 읽을 수 있는 Shelf의 게시물만 받는다. 메뉴 숨김과 실제 읽기 권한은 별개이며 홈의 shelves와 navigation은 메뉴 숨김을 따른다.

collection은 [공개 목록](canvas-feed.md)의 현재 계정/Board/Shelf/멤버/등급·제재 및 live/snapshot visibility 교집합 정책과 같은 SQL을 사용한다. 미공개 제목·요약·태그와 본문 JSONB는 조회하지 않으며 현재 visibility·소속·author는 읽는다. DB status=draft는 편집 lifecycle이며 publication이 없는 미게시 초안은 Owner 본인의 글도 표시하지 않는다. 표시 제목·요약·Tag는 마지막 공개본, Board/Shelf/author는 현재 관계이며 삭제된 author는 null이다. total/cursor/본문은 위젯 응답에 없다.

## 읽기 일관성과 한도

models/board.py의 기존 저장소가 홈 읽기 트랜잭션을 소유한다. PostgreSQL은 첫 조회 전 REPEATABLE READ READ ONLY, SQLite는 명시 BEGIN으로 계정/Board/member/grade/policy/shelves/layout과 공개 header/정렬 태그를 같은 snapshot에서 읽는다. 새 요청은 변경된 권한을 적용하며 이미 시작한 읽기는 이전 snapshot을 마칠 수 있다. 전달된 정보의 회수는 보장하지 않는다. 일반 공개 feed의 단일 statement 계약은 그대로 유지한다.

같은 source는 최대 limit으로 중복 제거한다. 최대 100개 고유 source를 하나의 ranked SQL로 조회하고 source별 최신 published_at/UUID 내림차순 최대 20개 header를 먼저 고른 뒤 고정 태그를 연결한다. 항목별 N+1·위젯별 서비스 호출·본문 SELECT는 없다. 응답은 최대 100위젯·위젯당 20 header·header당 10 Tag이며 중복 위젯은 각자의 limit만 잘라 사용한다. 높은 동시 처리량/대규모 Board SLA를 주장하지 않는다.

SQLite와 실제 고유 schema PostgreSQL에서 기본 문서 왕복, 현재 역할/등급, 관리/방문자 분리, CAS 단일 승자, 권한 회수의 lock 대기, flush/commit 실패 원자성, 기존 Canvas/publication/Tag/Asset/ref/outbox 보존과 Board 삭제를 검증한다. 비밀 source 비노출·메뉴 숨김·고정 header/Tag·본문 미조회·metadata와 hydration 사이의 변경 일관성도 확인한다. 원래 개발 DB/env/파일은 변경하지 않는다.


## Board 미디어 연계 — #59

홈/상세/by-slug의 BoardSummary는 현재 avatar/cover UUID와 허용 요약을 media batch로 읽는다. board_cover.widget_data.media는 같은 summary.cover이며 저장 layout의 source/asset_id/URL 금지는 유지한다. can_manage_media는 변경 API의 공통 구조 관리 가드로 계산한다. media 변경은 공용 Board revision만 갱신하고 저장 layout/layout_revision은 바꾸지 않는다.
