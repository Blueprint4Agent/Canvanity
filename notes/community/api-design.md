# MVP API 명세

[도메인](domain-model.md) · [권한](membership-policy.md)

## 공통 계약

아래는 전체 목표 API의 설계 명세다. 현재 구현된 개설/조회/빈 보드 삭제 API의 구체 계약과 화면은 [Board 개설 흐름](board-creation.md)을 우선한다. `/api/v1` 기준, snake_case, 신규 ID는 UUID, 기존 user_id는 정수다. Interest id는 기존 slug다. 도메인 예외는 기존 ServiceException/ErrorResponse(`detail.error/message/details`)와 도메인별 응답 생성기를 사용한다. Pydantic의 구조 검증 오류는 기존 FastAPI 422 배열을 유지한다. 새로운 422 도메인 오류는 기존 도메인 에러 DTO를 사용한다.

| 응답 | 기준                                                                       |
| ---- | -------------------------------------------------------------------------- |
| 200  | 조회/수정/가입/게시 성공. 바뀐 revision/capabilities 반환                  |
| 201  | Board/Shelf/Grade/Canvas/Tag 생성. Location 헤더에 리소스 경로             |
| 204  | 멤버 탈퇴·빈 Shelf 삭제·게시글 휴지통 이동 (Grade 대체 삭제는 200 목록 반환) |
| 401  | 인증이 필요한 액션의 토큰 없음/만료                                        |
| 403  | 볼 수 있는 객체에서 역할·등급·액션 부족                                    |
| 404  | 없음 또는 읽기 권한 없는 객체(비공개 Board/초안/제한 Shelf 포함)           |
| 409  | slug 중복·revision 충돌·마지막 Owner·기본 Shelf/등급 삭제·잘못된 상태 전이 |
| 413  | 본문/레이아웃 바이트 상한 초과(파싱 전 스트림/ingress 제한 포함)           |
| 422  | 입력 길이·enum·서로 다른 Board의 Shelf/등급·지원하지 않는 문서 버전/요소   |

인증 실패는 먼저 401, 인증된 사용자의 숨겨진 객체는 404로 응답한다. 접근 권한이 있는 객체의 액션 부족만 403이다. 모든 에러에 DB 원문·스토리지 키·비밀값을 포함하지 않는다.

수정 요청은 해당 aggregate의 `expected_revision`을 요구한다. Board/등급/정책/Shelf 순서·멤버 변경은 Board revision을 공유한다. Canvas 메타데이터는 metadata revision, 본문은 document revision, 공식 홈은 layout revision을 사용한다. Board/Shelf 변경 응답은 최신 board_revision을 반환한다. 충돌은 다음 형태다.

```json
{
    "detail": {
        "error": "BOARD_REVISION_CONFLICT",
        "message": "최신 정보를 다시 불러오세요.",
        "details": { "current_revision": 5 }
    }
}
```

목록은 새 피드에 한해 `limit`(기본 20, 1~100), `cursor`, `sort=latest`를 사용한다. 응답은 `{items,next_cursor}`이며 total은 노출하지 않는다. cursor는 버전·정렬·마지막 시각/ID·필터 해시를 Base64URL로 인코딩하고 길이 2,048자를 제한한다. 서명 없는 cursor는 신뢰하지 않고 재파싱/검증하며 매 조회에 권한 필터를 다시 적용한다. 동일 published_at은 UUID 내림차순으로 결정한다. 새 게시글/권한 변경 중의 완전한 snapshot pagination은 보장하지 않는다. 기존 page/page_size 기반 API는 그대로 둔다.

## Board·멤버십·등급 — #22

| Method  | Path                                 | 입력/결과·권한                                                                                                         |
| ------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| GET     | /boards                              | q 최대 200, interest_id 기존 slug, cursor. 조회 가능한 Board만                                                         |
| GET     | /boards/by-slug/{slug}               | UUID 상세와 같은 응답/권한. 정적 경로를 /{board_id}보다 먼저 등록                                                      |
| POST    | /boards                              | name/slug/description/rules/interest_ids/visibility/join_policy. 로그인 사용자                                         |
| GET     | /boards/{board_id}                   | 공개 정보 + 본인 membership/capabilities + revision. 타인 이메일 제외                                                  |
| PATCH   | /boards/{board_id}                   | expected_revision + 이름/소개/규칙/관심사/visibility/join_policy/status. Owner/Admin, status archived는 Owner만        |
| GET     | /boards/{board_id}/home              | 기본 Board·허용 Shelf·공개 snapshot 목록·layout/capabilities. 동적 위젯도 현재 방문자 기준                             |
| POST    | /boards/{board_id}/join              | public/open만. 활성 가입은 같은 결과 200. 탈퇴/제재 상태를 임의 초기화하지 않음                                        |
| GET     | /boards/{board_id}/membership        | 본인 role/status/grade/board_revision/capabilities                                                                     |
| DELETE  | /boards/{board_id}/membership        | 활성 비Owner 탈퇴. repeated absent 204. banned/suspended 기록은 탈퇴로 제거하지 않음                                   |
| GET     | /boards/{board_id}/members           | Owner/Admin은 전체, Moderator는 제재 대상용 공개 필드만. 일반 회원은 이 경로 403                                       |
| POST    | /boards/{board_id}/members           | user_id/expected_revision/reason. private 수동 초대 Owner/Admin, 기본 뉴커머 등급 active로 등록. 기존 banned 우회 금지 |
| PATCH   | /boards/{board_id}/members/{user_id} | expected_revision/reason + role/status/grade_id. 각 필드별 위계 검사                                                   |
| GET     | /boards/{board_id}/grades            | 조회 가능한 Board의 이름·순위·기본 등급, 사용자 개인정보 없음                                                          |
| POST    | /boards/{board_id}/grades            | expected_revision/reason/name/rank. Owner/Admin, 최대 20개. 201 grade/board_revision                                   |
| PATCH   | /boards/{board_id}/grades/{grade_id} | expected_revision/reason + name 또는 is_default:true. rank는 order API에서만 변경. 200 grade/board_revision            |
| PATCH   | /boards/{board_id}/grades/order      | expected_revision/reason/grade_ids(전체). rank를 10 단위로 재부여. 200 items/board_revision                             |
| DELETE  | /boards/{board_id}/grades/{grade_id} | expected_revision/reason/replacement_grade_id. 참조·기본값 이동, 마지막 등급 409. 200 items/board_revision             |
| GET/PUT | /boards/{board_id}/policies          | GET은 Owner/Admin. PUT expected_revision/actions(전체 4액션), 역할·등급 정책 원자적 갱신                               |
| GET     | /boards/{board_id}/member-audit      | Owner/Admin, cursor·기간(최대 180일). 개인정보 최소 필드                                                               |

MVP public→private 전환은 기존 open 멤버가 유지되며 join_policy=invite를 같은 요청에 요구한다. private→public은 공개 snapshot·파일 노출 범위가 넓어짐을 UI에서 명시하고 Owner만 허용한다. Admin은 visibility 변경 불가다. Board archived→active는 Owner가 명시적으로 복원한다. suspended 설정/해제는 이 일반 API에서 거부한다.

```json
{
    "name": "AI Agent 연구소",
    "slug": "ai-agent-lab",
    "description": "에이전트 설계와 개발 경험을 공유합니다.",
    "interest_ids": ["ai", "development"],
    "visibility": "public",
    "join_policy": "open"
}
```

interest_ids 값은 설명용이며 실제 GET /interests의 활성 id만 수락한다. Board 응답은 id/slug/name/description/rules/visibility/join_policy/status/interest_ids/revision, 본인 membership(없으면 null), capabilities를 반환한다. owner_id는 공개 계정 ID만 반환하며 이메일/인증정보는 제외한다.

Owner 전용 `POST /boards/{board_id}/ownership-transfer`는 expected_revision/target_user_id/reason을 받는다. 기존 Owner→Admin, 대상 active 멤버→Owner, owner_id 변경과 감사를 원자적으로 처리한다. generic member PATCH의 role=owner는 422다. `DELETE /boards/{board_id}`는 Owner만 archived 상태에서 `{expected_revision,confirm_slug}`로 요청한다. 게시글 등 하위 DB 데이터 삭제와 파일 정리 outbox를 원자적으로 기록하고 204를 반환한다. sole Owner도 보관→명시적 영구 삭제로 계정 삭제 전제조건을 해소할 수 있다. 계정 삭제 소유 검사는 이 종료 경로와 함께 출시한다.

## Shelf — #23

| Method   | Path                             | 계약                                                                                                                          |
| -------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| GET/POST | /boards/{board_id}/shelves       | GET 방문자가 읽을 수 있는 메뉴만, POST 운영자. 이름/slug/description/icon/purpose/classification/is_visible/expected_revision |
| PATCH    | /shelves/{shelf_id}              | Owner/Admin, 같은 필드·expected_revision. board_id 변경 금지                                                                  |
| DELETE   | /shelves/{shelf_id}              | expected_revision, 빈 비기본 Shelf만. 초안/휴지통도 비어 있지 않음으로 계산                                                   |
| PATCH    | /boards/{board_id}/shelves/order | expected_revision/shelf_ids 전체. 운영자                                                                                      |
| GET/PUT  | /shelves/{shelf_id}/policies     | Owner/Admin. PUT expected_revision/actions, null 액션은 상속                                                                  |
| GET      | /shelves/{shelf_id}/canvases     | 현재 읽기 정책을 적용한 공개 snapshot 최신순 목록                                                                             |

기존 예제의 `write_policy`는 독립 권한 원본으로 저장하지 않는다. 상세 응답에 본인 capabilities와 정책 요약을 제공한다. 목적(purpose=general/notice)과 분류 방식(classification=manual)을 분리한다. is_visible=false는 메뉴에서만 숨기며 직접 URL 접근은 실제 읽기 정책을 따른다. smart 입력은 422다.

## Canvas 메타데이터·문서·게시 — #8/#7

| Method | Path                            | 계약                                                                                                             |
| ------ | ------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| POST   | /boards/{board_id}/canvases     | shelf_id/title/tag_ids, create_canvas capability. 초안 메타와 빈 본문 생성                                       |
| GET    | /canvases/{canvas_id}           | 작성자는 초안 메타/문서 revision, 다른 사용자는 공개 snapshot 메타만. capabilities와 view=draft/publication 명시 |
| PATCH  | /canvases/{canvas_id}           | 작성자, expected_revision + title/summary/shelf_id/tag_ids/thumbnail_asset_id/visibility/status. 허용 전이만     |
| DELETE | /canvases/{canvas_id}           | expected_revision, 작성자 휴지통 또는 운영자 공개글 moderation. 204                                              |
| POST   | /canvases/{canvas_id}/restore   | 작성자, expected_revision. 휴지통 30일 내 draft 복구                                                             |
| GET    | /canvases/{canvas_id}/document  | 작성자는 기본 draft, 타인은 publication. view=draft를 명시해도 권한 우회 불가. revision/document 반환            |
| PUT    | /canvases/{canvas_id}/document  | 작성자+현재 작성 등급, expected_revision/document. 원자 CAS, 성공 revision 반환                                  |
| POST   | /canvases/{canvas_id}/publish   | 작성자+작성 권한, expected_document_revision/expected_metadata_revision                                          |
| POST   | /canvases/{canvas_id}/unpublish | 작성자 또는 공개글 moderation 운영자, expected_revision. 이미 draft면 상태 확인 후 200                           |
| GET    | /canvases                       | Plaza용 공개 snapshot 조회. interest_id/tag_id/board_id/cursor/limit, 현재 권한 필터                             |
| GET    | /boards/{board_id}/canvases     | 동일 공개 목록 + Board 범위                                                                                      |
| GET    | /boards/{board_id}/my-canvases  | 로그인 본인 초안/공개/보관/휴지통, status 필터. 프로필 My Canvas와 별도 데이터                                   |

author_id/board_id/published_at/publication_revision은 서버 전용 필드다. DTO extra='forbid'로 과다 필드를 422로 거부한다. metadata revision과 document revision을 혼용하지 않는다.

```json
{
    "expected_revision": 4,
    "document": {
        "schema_version": 1,
        "engine": { "name": "excalidraw", "version": "0.18.1", "adapter_version": 1 },
        "settings": { "background": "#F8F7F4", "grid": "dots", "width": 3200, "height": 2100 },
        "nodes": [],
        "edges": []
    }
}
```

publish 응답은 metadata_revision/document_revision/publication_revision/published_at을 반환한다. 파일 변환/미리보기 작업을 큐에 넣었다면 성공한 미리보기처럼 표시하지 않고 preview_status=pending/ready/failed로 구분한다. 공개 이미지 썸네일은 해당 publication_revision에 귀속시키고 미생성 시 기본 미리보기를 사용한다.

## Tag·에셋·공식 레이아웃

- #24 GET /tags?q=…&limit=20, POST /tags `{name}`. 정규화 중복 생성은 기존 Tag를 200, 신규는 201. 생성/검색 요청은 기존 rate-limit 패턴으로 사용자별 분당 30회를 적용한다. Canvas 연결은 metadata PATCH로만 한다.
- #6 POST /canvases/{id}/assets (multipart 이미지 한 개), GET /canvases/{id}/assets/{asset_id}, DELETE 동일 경로(미참조 업로드만). 실제 형식 PNG/JPEG/WebP/GIF·8 MiB·16MP, 본문/공개본에 연결된 asset 삭제 409. 기존 object storage 사용·서명 URL 영속 금지. 세부 이미지 변환/애니메이션 정책은 #6에서 실제 구현과 확정한다.
- #25 PUT /boards/{id}/layout `{expected_revision,document:{schema_version,widgets}}`, Owner/Admin. GET home에 layout_revision 포함. 엔진 nodes/edges 문서는 422.
- 댓글·좋아요·구독·통계 API는 #26에서 추가하며 Shelf create_comment/react 정책을 재사용한다. 자동 승급 API와 Smart Shelf endpoint는 아직 노출하지 않는다.

## 화면·상태 소유권

Plaza /home, 내 프로필 홈 /my-canvas, Board 탐색 /board는 유지한다. Board 상세 /b/{slug}, Shelf /b/{slug}/s/{shelf_slug}, 게시글 /c/{uuid}, 편집 /c/{uuid}/edit를 추가한다. slug는 서버 해석 API에서 UUID로 변환하고 권한은 매번 검사한다.

페이지가 도메인 훅을 호출하고 훅이 생성 타입 기반 API·로딩/오류/충돌 상태를 소유한다. 편집기 어댑터는 작업 문서·undo 이력, 저장 훅은 서버 revision·저장 큐·계정/document epoch, 카메라 훅은 팬/줌·선택 임시 상태를 소유한다. 카메라 변화로 자동 저장하거나 페이지를 강제 재마운트하지 않는다.

1단계는 설계였으며 후속 Board 개설 구현은 라우터/OpenAPI/생성 타입을 함께 변경했다. 구현 때 `make contract-export` → 루트 계약을 frontend/contracts로 명시 복사 → `make frontend-api-generate` → `make contract-check frontend-api-check frontend-typecheck` 순서로 동기화한다. 제품 E2E는 actual PostgreSQL/로컬 object storage까지 왕복하고 mock/UI probe 성공을 제품 완료로 기록하지 않는다.


## 공개 가입·탈퇴 구현 계약

`POST /boards/{board_id}/join`은 200 MembershipSummary(role/status/grade_id/grade_name), `DELETE /boards/{board_id}/membership`은 204다. 둘 다 Bearer 세션 전용이다. Owner 탈퇴는 409 BOARD_OWNER_CANNOT_LEAVE, 초대 전용/신규 보관 보드 가입과 제재 상태 변경 우회는 거부한다. 성공한 변경은 Board revision을 증가시키고 기존 active 가입·이미 탈퇴한 공개 보드의 반복 탈퇴는 상태를 변경하지 않는다. private 보드의 비회원에게는 탈퇴 시에도 404로 존재를 숨긴다. 현재 기본 등급을 사용하며 요청에서 역할/등급을 지정하는 기능은 없다.


## 회원 운영 API 구현 — #31

[회원 운영 계약](member-administration.md)을 따른다. GET members는 Owner/Admin의 관리 항목과 Moderator의 최소 공개 제재 대상 항목을 구분한다. PATCH members는 expected_revision/reason과 role/status/grade_id를 받고 필드 전체의 권한을 원자적으로 검사한다. GET member-audit의 since/until은 시간대 포함 필수 입력이며 최대 180일, target_user_id와 cursor를 지원한다. 목록/감사 정렬은 시각·식별자 내림차순이다. 이번 변경은 UI와 등급 정의 CRUD를 포함하지 않는다.
