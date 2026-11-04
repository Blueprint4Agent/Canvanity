# Canvas 초안 본문 저장 — #47 / #7

작성자 전용 `PUT /api/v1/canvases/{canvas_id}/document`를 제공한다. [객체 스키마](canvas-content-schema.md)와 [초안 메타데이터](canvas-drafts.md), [이미지 에셋](canvas-assets.md)을 같은 저장 트랜잭션에 연결한다. 구현·검증·PR 게시·main 병합은 [#47](https://github.com/Blueprint4Agent/Canvanity/issues/47)에서 구분한다. 자동 저장·충돌 복구 UI·제품 편집기는 #7의 후속이고, [#51 게시/공개본 단건](canvas-publication.md)은 현재 초안의 source revision을 고정한다. [공개 목록/Plaza #53](canvas-feed.md)은 공개 source clock과 snapshot header만 읽는 별도 계약이다.

## 요청·응답

Bearer 세션 전용이며 API Key는 허용하지 않는다. 요청은 `expected_revision`과 `document: CanvasContent`만 받는다. `expected_revision`은 **본문** revision으로, 메타데이터의 `canvas.revision`과 별개인 엄격한 정수 0~2^63−1이다. 문자열·소수·boolean·null·추가 필드를 거부한다.

```json
{
  "expected_revision": 0,
  "document": {
    "schema_version": 1,
    "engine": { "name": "excalidraw", "version": "0.18.1", "adapter_version": 1 },
    "settings": { "background": "#F8F7F4", "grid": "dots", "width": 3200, "height": 2100 },
    "nodes": [],
    "edges": [],
    "element_order": []
  }
}
```

성공은 200 `{ "revision": 1, "view": "draft" }`와 `Cache-Control: private, no-store`다. 본문을 응답에 다시 넣지 않는다. GET `/document`로 동일 객체·레이어 순서와 최신 revision을 읽고, 메타데이터 GET의 `document_revision`도 같은 버전을 반환한다. 같은 내용의 재저장도 현재 기대 revision을 확인하고 본문 revision을 1 증가시킨다. 제목·상태·소속·[태그 연결](canvas-tags.md)·메타데이터 revision/updated_at은 변경하지 않는다. 반대로 태그 PATCH도 본문 revision/본문·이미지 참조/outbox를 보존한다.

| 실패 | 상태·계약 |
| --- | --- |
| 본문 revision 불일치 또는 최대값 도달 | 409 `CANVAS_DOCUMENT_REVISION_CONFLICT`, `details.current_revision`. 메타데이터의 `CANVAS_REVISION_CONFLICT`와 구분 |
| 현재 Shelf 읽기/작성 권한 부족·보관 Board | 403 `CANVAS_FORBIDDEN` |
| 휴지통 편집 | 409 `CANVAS_INVALID_STATE` |
| 타인·없는 Canvas, 현재 비활성 멤버·정지 Board | 기존과 같은 404 `CANVAS_NOT_FOUND` |
| 비활성/삭제 계정 | 기존 인증의 404 `USER_NOT_FOUND`; 세션 없음은 401 |
| 잘못된 객체·버전·기대 revision·정규화 문서 크기 | FastAPI 입력 검증 422 |
| 없는/다른 Board·Canvas/pending/deleting 이미지 | 422 `ASSET_INVALID_REFERENCE` |
| 원시 요청 바이트 상한 초과 | 413 `CANVAS_DOCUMENT_TOO_LARGE` |
| 본문 행 누락·DB 갱신/flush/commit 실패 | 503 `CANVAS_UNAVAILABLE` |

OpenAPI는 입력 검증의 `detail: []`와 에셋 도메인 오류의 `detail: {error,message}`를 모두 422의 대안으로 선언한다. 다른 저장소의 객체 정보나 SQL 오류 원문은 응답하지 않는다.

## 입력 상한과 권한

새 PUT의 전용 `APIRoute` 전송 어댑터는 실제 스트림을 세어 JSON 디코딩 **전** 최대 2 MiB + 64 KiB(2,162,688바이트)를 허용한다. Content-Length가 없거나 거짓으로 작아도 같은 상한을 적용하고 초과 chunk 뒤의 데이터는 더 읽지 않는다. 유효한 요청은 공개 `Request(scope, receive)`로 재생하여 FastAPI의 일반 Body DTO·의존성·오류 처리를 유지한다. GET·메타데이터·파일 업로드에는 이 제한을 적용하지 않는다.

64 KiB는 요청 envelope/공백 여유다. `utils/canvas_limits.py`의 기술 상수를 모델과 전송 어댑터가 공유한다. `CanvasContent` 자체는 정규화 compact UTF-8 JSON 2 MiB 이하이며, Text/Image/Drawing/Shape/Edge·엔진 버전·기하·연결·순서·개수 검증을 그대로 사용한다. 전송 상한은 413, 전송 범위 안에서 정규화 문서 상한을 넘기면 422다. 두 제한 모두 성능 SLA가 아니다.

`CanvasAccessService`는 잠금을 얻은 뒤 현재 활성 계정·작성자·active 멤버·active Board와 Shelf `read_canvas`/`create_canvas`를 재검사한다. `CanvasService`는 draft 상태를 확인한다. Owner/Admin/Moderator와 앱 관리자도 타인 초안을 우회하지 않는다. 등급 강등·Shelf 제한 후 자신의 GET 복구는 유지하고 쓰기는 거부한다. 현재 `capabilities.edit_document`는 `draft`이고 현재 작성 정책을 만족할 때만 true다. 보관/휴지통에서는 false다.

## CAS·참조·정리의 원자성

세션·SQL·ORM 쓰기·트랜잭션·드라이버 오류 변환은 기존 `models/canvas.py`와 `models/asset.py`에 둔다. 서비스는 저장소/공유 가드를 DI로 받고 세션을 열거나 전달하지 않는다. 별도 Repository 파일과 파일 I/O는 추가하지 않는다.

잠금 순서는 **Board → 활성 User 공유 잠금 → Canvas → CanvasDocument → 정렬한 해당 Canvas의 Asset → outbox**다. 계정 삭제의 User→Canvas SET NULL 순서를 지키고, Board 정책/회원 변경·정리 claim과 직렬화한다. 문서 행을 잠근 뒤 `UPDATE ... WHERE canvas_id=:id AND revision=:expected AND revision<MAX RETURNING revision`으로 최종 CAS를 수행한다. 동일 expected revision의 두 연결 중 하나만 성공하고 뒤 요청은 현재 revision의 409를 받는다.

같은 `CanvasTransaction.save_document`가 실제 `CanvasImageNode.content.asset_id`의 중복 없는 집합을 추출하고 같은 세션의 `AssetTransaction.replace_refs(scope="draft")`를 호출한다. 새 참조는 해당 Board/Canvas의 ready 에셋이어야 하며, 조회/잠금도 그 소속으로 한정한다. 별도 에셋 트랜잭션이나 서비스 간 비공개 호출로 분리하지 않는다.

draft 참조만 교체하고 publication 참조는 보존한다. 어느 scope든 참조가 남으면 `expires_at=null`과 protected outbox를 유지한다. 마지막 참조가 없어질 때만 기존 24시간 미사용 유예/outbox를 다시 예약한다. ready의 `expires_at`은 정리 예정 시각이며 독립적인 참조 금지 시각이 아니다. 저장이 먼저 잠금을 얻으면 참조와 protected 작업이 정리를 막고, worker가 먼저 deleting으로 claim하면 저장이 에셋 검증에서 실패한다.

CAS 뒤 참조 검증·FK/flush·commit이 실패하면 본문·revision·참조·TTL·outbox가 함께 롤백된다. commit 응답만 유실되면 실제 저장이 완료됐을 수 있으므로 파일을 보상 삭제하지 않는다. 클라이언트는 GET으로 현재 revision/본문을 확인해야 한다.

## 검증과 남은 범위

API 검사는 세션·엄격한 입력·크기 경계·작은 응답·오류 대안을 확인한다. 실제 SQLite는 5타입 저장→GET, 동일 revision 경쟁, 중복/일부/전체 이미지 제거, publication 보호, 현재 권한 회수, 잘못된 참조와 flush/commit/불확실한 commit을 검증한다.

`tests/integration/api/v1/canvas/test_canvas_document_postgres.py`는 `CANVANITY_TEST_POSTGRES=1`로 명시 실행한다. 로컬 PostgreSQL에 매번 고유 schema를 생성하고 실제 migration·JSONB·두 연결 CAS·FK/flush/commit 롤백·Board 잠금 대기 중 등급 회수·저장/cleanup 양방향 경쟁을 확인한다. 임시 파일만 쓰고 schema 삭제를 재확인하며 기존 DB/Board/프로필 파일을 보존한다. 기본 전체 테스트에서는 이 opt-in 검사가 skip되므로 실제 실행 결과는 [작업 기록](../../worklog/0292-canvas-document-save.md)에 별도로 남긴다.

기존 0026/0027 테이블과 제약을 사용하여 새 migration은 없다. [자유 Tag](canvas-tags.md)와 [게시/공개본 단건 열람](canvas-publication.md)은 별도 계약으로 연결한다. 게시 뒤 PUT도 draft만 바꾸고 source document revision과 공개 내용은 재게시까지 유지한다. 자동 저장 큐/오프라인 복구·실시간 편집·공개 목록·UI·운영 배포는 포함하지 않는다.
