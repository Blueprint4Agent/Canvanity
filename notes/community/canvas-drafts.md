# Canvas 초안·메타데이터 기반 — #8

작성자 전용 draft/trashed 메타데이터와 JSONB 초기 문서, 같은 Board의 Manual Shelf 소속을 제공한다. 선행 초안 PR #41의 688bbf8을 기준으로 분리했고 [본문 저장 #47](canvas-document-save.md)이 편집 문서 PUT/CAS를 연결한다. 구현·검증·원격 게시와 main 병합/운영 배포는 이슈/PR에서 별도로 확인한다.

## API

모든 경로는 /api/v1 기준이다. 쓰기는 Bearer 세션 전용이고 GET은 [게시 계약](canvas-publication.md)의 optional Bearer/view를 사용한다. 모든 성공 응답은 Cache-Control: private, no-store를 반환한다.

| Method | Path | 계약 |
| --- | --- | --- |
| POST | /boards/{board_id}/canvases | shelf_id/title, 선택 summary/visibility/tag_ids. 현재 읽기/작성 가능한 같은 Board Manual Shelf에 초안·빈 본문·태그 연결을 원자 생성 |
| GET | /canvases/{canvas_id} | 현재 active 멤버인 작성자의 초안 메타데이터·본문 revision·capabilities |
| PATCH | /canvases/{canvas_id} | expected_revision + title/summary/shelf_id/visibility/tag_ids의 제공 필드. 현재 원본/대상 Shelf 읽기·작성 권한 요구 |
| DELETE | /canvases/{canvas_id} | expected_revision. 작성자 휴지통 이동, 204와 X-Canvas-Revision |
| POST | /canvases/{canvas_id}/restore | expected_revision. 현재 작성 권한과 30일 복구 기간을 검사해 draft 복원 |
| GET | /canvases/{canvas_id}/document | 작성자의 현재 초안 본문과 document revision |
| PUT | /canvases/{canvas_id}/document | expected_revision/document. 현재 작성 권한·draft·실제 Asset를 검증하고 본문/revision/draft 참조를 원자 저장 |

생성은 201과 Location: /api/v1/canvases/{id}를 반환한다. 생성/메타데이터 조회·수정/복구 응답은 {canvas, document_revision, view:"draft", capabilities}다. canvas.revision은 메타데이터 revision이다. 본문 조회 응답은 {document, revision, view:"draft"}이며 여기의 revision은 본문 버전이다. draft 응답에는 현재 publication_revision/요약과 publish/unpublish capabilities도 반환한다. GET은 기본 작성자 draft/타인 publication, 명시 view=draft/publication을 허용하며 공개 whitelist/권한은 [게시 계약](canvas-publication.md)을 따른다.

title은 공백 제거 후 1~200자, summary는 최대 500자다. visibility=members가 기본이고 public도 설정할 수 있으나 **명시적으로 게시하기 전 초안은 작성자 전용**이다. 게시 뒤에도 metadata/본문/태그 수정은 draft만 바꾸고 공개본은 재게시 전까지 고정된다. [자유 Tag](canvas-tags.md)의 tag_ids는 최대10개 고유 UUID이며 생성 시 기본 빈 배열, PATCH 생략은 유지/빈 배열은 해제다. 응답 canvas.tags는 정렬한 ID/표시명 요약이다. id/author_id/board_id/status/게시 시각·에셋·본문 등 지원하지 않는 필드는 extra=forbid로 422다. PATCH는 최소 한 필드를 요구하고 명시적 null은 거부한다. expected_revision은 JSON 정수 0~2^63-1이며 문자열/소수/bool은 거부한다.

## 작성자와 현재 권한

계정과 Board가 유효하고 현재 해당 Board의 active 멤버인 작성자만 읽을 수 있다. 탈퇴/pending/제재·Board 정지와 다른 작성자·없는 객체는 동일 CANVAS_NOT_FOUND 404다. Owner/Admin/Moderator·앱 전역 관리자와 높은 활동 등급도 타인의 초안을 읽거나 편집하지 못한다. 공개 visibility도 이 경계를 넓히지 않는다.

낮은 등급이나 Shelf 읽기 제한은 자신의 초안 조회/휴지통 이동을 막지 않는다. 편집·생성·복구는 현재 Shelf read_canvas와 create_canvas 정책을 모두 만족해야 한다. 이동은 원본/대상 양쪽 정책을 검사하고 같은 Board만 허용한다. 메뉴 숨김은 작성 권한이 아니며 공지의 staff_only를 그대로 적용한다. 재가입하면 기존 자신의 초안 읽기를 복구하지만 현재 등급이 부족하면 편집은 계속 거부한다.

Board archived는 작성자 조회만 허용하고 변경/휴지통/복구/새 생성은 403이다. suspended는 404다. capabilities는 read_document/edit_metadata/edit_document/trash/restore를 제공한다. edit_document는 draft와 현재 Shelf 읽기/작성 정책을 모두 만족해야 한다. 낮은 등급의 작성자는 read_document/trash와 현재 공개본 unpublish가 가능하고, 보관된 Board에서는 읽기만 허용된다. publish는 현재 Shelf 읽기/작성 권한, unpublish는 현재 active 작성자/멤버/Board를 요구한다.

## 문서·저장·동시성

0026_canvas_drafts는 canvases와 canvas_documents를 추가한다. 소속 (board_id, shelf_id)는 shelves의 복합 유니크를 참조하고 삭제는 RESTRICT다. 작성자 FK는 기존 설계의 SET NULL을 사용한다. 계정 삭제 시 초안 메타데이터/문서는 남지만 초안 읽기 권한을 다른 사용자에게 주지 않는다. 이미 게시된 공개본은 현재 author_id=null을 반영하고 현재 공개 읽기 정책 아래 유지한다.

본문은 schema_version=1, engine(excalidraw 0.18.1/adapter 1), settings(배경 #F8F7F4·dots·3200×2100), 빈 nodes/edges/element_order로 초기화한다. 이는 기존 검증 어댑터의 포맷을 따른 초기값이며 제품 편집기의 채택·설치를 의미하지 않는다. [객체 스키마](canvas-content-schema.md)는 Text/Image/Drawing/Shape/Edge의 실제 출력 타입과 문서 내부 검증을 정의한다. 생성 데이터는 계속 비어 있고, [본문 저장](canvas-document-save.md)이 동일 모델을 PUT 입력으로 받고 실제 에셋 소속/ready·draft 참조와 함께 저장한다.

세션·SQL·ORM 쓰기·트랜잭션·드라이버 오류 변환은 기존 패턴대로 models/canvas.py 안의 CanvasRepository/CanvasTransaction이 소유한다. 같은 세션에 BoardTransaction을 조합해 Board 권한 데이터를 읽고, CanvasService는 저장소와 공유 CanvasAccessService를 생성자 DI로 사용한다. 공유 가드는 BoardPermissionService로 정책을 평가하며 이미지 서비스도 같은 작성자 경계를 사용한다. 별도 Repository 파일이나 다른 서비스 private 호출은 없다.

변경은 Board→활성 User 공유 잠금→Canvas 순서다. User 잠금은 Canvas 행보다 먼저 얻어 계정 삭제의 User→Canvas SET NULL 순서와 충돌하지 않게 한다. 정책/역할 변경과 같은 Board 잠금을 사용해 변경 commit 뒤의 새 쓰기가 오래된 권한을 사용하지 않도록 한다. GET은 Board/User/Canvas 공유 잠금과 SQLite 읽기 transaction으로 현재 정책과 view를 일관되게 읽으며 진행 중인 요청의 snapshot을 마칠 수 있다.

메타데이터 변경·휴지통/복구는 metadata revision을 증가시키며 현재 본문과 document revision은 유지한다. 휴지통은 공개 snapshot/publication 참조를 제거하고 공개 상태 token도 증가시킨다. 복구는 자동 재게시하지 않는다. 메타데이터 no-op도 현재 권한과 revision을 검사하고 버전을 늘리지 않는다. stale 메타데이터는 CANVAS_REVISION_CONFLICT 409와 current_revision, 본문 CAS는 별도 CANVAS_DOCUMENT_REVISION_CONFLICT 409다. 본문은 같은 내용의 재저장도 기대 revision을 검사해 증가시킨다. 휴지통 편집은 CANVAS_INVALID_STATE 409다. 실패 시 부분 메타데이터/본문을 남기지 않고 CANVAS_UNAVAILABLE 503으로 변환한다. 복구는 trashed_at으로부터 30일 미만이며 정확히 30일부터 CANVAS_RESTORE_EXPIRED 409다. 자동 purge는 아직 없다.

## Shelf·Board 삭제 연계와 후속

Shelf 삭제는 초안·휴지통·작성자가 삭제된 문서를 모두 비어 있지 않음으로 계산해 SHELF_NOT_EMPTY 409다. 같은 Board의 다른 Shelf로 문서를 옮기면 비기본 빈 Shelf를 삭제할 수 있다. active 빈 Board 되돌리기도 Canvas가 하나라도 있으면 409다. 보관된 Board의 Owner 확인 삭제는 현재 모든 CanvasDocument/Canvas를 Shelf보다 먼저 같은 트랜잭션에서 정리하고 다른 Board/계정/프로필 파일을 보존한다.

[이미지 에셋](canvas-assets.md)이 업로드/조회/미참조 삭제·참조 FK·Board 삭제 outbox/worker를 연결한다. 객체 타입·문서 내부 validator는 [객체 스키마](canvas-content-schema.md), 문서 PUT/CAS·본문과 draft 참조의 원자 동기화는 [#47 저장 계약](canvas-document-save.md), 사전 검색/생성과 metadata 태그 연결은 [#49 태그 계약](canvas-tags.md)을 따른다. #7 자동 저장/복구 UI, #24 태그 UI/발견, #51 [게시/공개본 단건 열람](canvas-publication.md)은 별도 구현 계약이며 #8 공개 목록·cursor·Plaza·UI는 후속이다. 자동 purge/휴지통 영구 삭제·운영자 공개글 moderation은 해당 수명주기와 함께 추가한다. 이번 최소 기반을 #8 전체 완료로 표시하지 않는다.
