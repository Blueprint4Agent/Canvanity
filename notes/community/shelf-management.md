# Shelf 관리·등급별 정책 — #23

현재 구현은 Manual Shelf 관리와 현재 권한 조회, Board 기본/Shelf 재정의 정책 API다. 제품 UI는 보류한다. 선행 초안 PR #40의 9cae95f를 기준으로 분리하며 main 병합은 이슈/PR에서 별도로 확인한다.

## API와 변경 계약

모든 경로 앞에 /api/v1을 붙인다. 변경 요청은 expected_revision(현재 Board revision)과 공백 제거 후 1~500자의 reason을 요구한다. 쓰기·정책 조회는 Bearer 전용이다. 앱 전역 관리자 역할과 Curator 등급만으로 관리 권한을 얻지 못한다.

| Method | Path | 동작 |
| --- | --- | --- |
| GET | /boards/{board_id}/shelves | 방문자가 읽을 수 있는 is_visible 메뉴만 반환. manage=true는 현재 Owner/Admin 전용 관리 목록 |
| GET | /shelves/{shelf_id} | 현재 읽기 정책을 검사하는 직접 조회. 숨김은 접근 금지가 아님 |
| POST | /boards/{board_id}/shelves | 현재 active Owner/Admin. 이름/slug/설명/icon/purpose/classification/is_visible, 뒤에 추가 |
| PATCH | /shelves/{shelf_id} | 같은 표시 필드만 수정. board_id/is_default/sort_order 변경 금지 |
| PATCH | /boards/{board_id}/shelves/order | shelf_ids에 숨김을 포함한 같은 Board의 전체 ID를 중복 없이 제공 |
| DELETE | /shelves/{shelf_id} | 현재 비기본 Shelf 삭제. 마지막 Shelf도 보호 |
| GET/PUT | /boards/{board_id}/policies | Owner/Admin의 4액션 기본 정책 조회/전체 교체 |
| GET/PUT | /shelves/{shelf_id}/policies | Owner/Admin의 4액션 재정의 조회/전체 교체. null 액션은 상속 |

name은 공백 제거 후 1~80자, slug는 3~64자의 소문자/숫자와 단일 하이픈 구분, description은 최대 2,000자, icon은 1~40자다. purpose=general|notice와 classification=manual을 분리한다. smart·알 수 없는 필드·명시적 null PATCH는 422다. bool 필드는 실제 JSON bool만 받는다. 순서는 전용 API에서만 바꾸고 최대 100개로 전체 관리/정렬 응답을 제한한다. 동일 Board slug 중복은 409이며 다른 Board의 동일 slug는 허용한다.

생성은 201과 Location: /api/v1/shelves/{id}, 변경/직접 조회는 200 {shelf, board_revision}, 목록/순서는 200 {items, board_revision}다. 일반 목록은 제한/숨김 항목의 제목이나 개수·별도 total을 반환하지 않는다. 관리 목록은 숨김/읽기 제한 항목도 구성할 수 있도록 반환하며 capabilities는 실제 현재 권한(읽기가 막히면 작성 등도 false)을 유지한다. Shelf ID 경로의 비공개/제한/없는 객체는 같은 SHELF_NOT_FOUND 404를 반환한다. 삭제는 204와 X-Board-Revision 헤더다. 모든 성공 응답은 Cache-Control: private, no-store다.

## 정책과 운영 역할

actions는 read_canvas/create_canvas/create_comment/react 네 키를 모두 요구한다. Board 기본 정책은 null을 허용하지 않는다. Shelf actions는 각 키의 null을 허용하며 해당 재정의 행을 삭제한다. 부분 PATCH로 오해하지 않도록 누락/추가 액션은 422다. Shelf 정책 응답에는 actions(재정의)와 effective_actions(현재 기본값을 합친 정책), board_revision을 반환한다.

각 액션은 audience, min_grade_id, staff_only, staff_bypass로 구성한다. 허용 형태는 다음과 같다.

- public 읽기: audience=public, min_grade_id=null, staff_only=false. 작성/댓글/반응의 public 입력은 422다.
- 등급: audience=members, 같은 Board의 min_grade_id, staff_only=false. 현재 rank를 비교하고 staff_bypass는 활성 Owner/Admin/Moderator의 최소 등급만 우회한다.
- 운영진 전용: audience=members, min_grade_id=null, staff_only=true. 일반 회원은 높은 등급이어도 거부한다.

private Board의 public 정책은 active 멤버 경계를 넓히지 않는다. pending은 공개 읽기만 가능하고 suspended/banned 멤버와 suspended Board는 404다. archived는 읽기·관리 설정 조회만 가능하며 쓰기는 403이다. 모든 검사는 현재 DB 상태로 하므로 같은 토큰으로 요청해도 승급·강등·등급 순서·정책 변경을 즉시 반영한다. Board 홈도 같은 shelf_capabilities 평가기를 사용한다. Owner/Admin의 정책 관리 권한은 Shelf 읽기 등급과 분리하여 본인의 읽기를 제한한 뒤에도 설정을 복구할 수 있다.

공지 Shelf의 create_canvas/create_comment는 명시적 staff_only 재정의를 유지한다. 생성과 general→notice 전환 시 저장소가 이를 준비하고, 공지 정책을 null/일반 등급 정책으로 낮추려는 요청은 SHELF_INVALID_POLICY 422다. notice→general 전환은 기존 재정의를 보존하므로 상속으로 되돌리려면 정책 PUT을 명시적으로 수행한다.

## 저장 책임·동시성·감사

ShelfService는 BoardRepository와 BoardPermissionService를 생성자 DI로 사용한다. SQL·세션·ORM 쓰기·잠금·감사/revision·DB 오류 변환은 기존 app/models/board.py의 Repository/Transaction이 소유한다. 새 Repository 파일/테이블/migration을 추가하지 않는다.

모든 변경은 Board 행을 잠근 뒤 현재 역할/상태와 expected_revision을 검사한다. Shelf ID로 Board를 해석한 뒤 잠금 아래 Shelf를 다시 읽어 삭제 경쟁의 오래된 객체를 사용하지 않는다. 정렬은 전체 ID를 검사하고 변경·감사·revision 증가를 한 트랜잭션으로 저장한다. 같은 revision의 경쟁 변경은 하나만 성공하고 다른 요청은 BOARD_REVISION_CONFLICT 409다. no-op도 현재 권한과 revision을 검사하되 revision/감사는 추가하지 않는다. 실패는 전체 롤백하고 정규화된 BOARD_UNAVAILABLE 503으로 반환한다.

회원 감사 API는 shelf_change/policy_change에 허용 DTO만 반환한다. Shelf 감사는 이전/이후 표시 상태와 필요 시 정책을, 정책 감사는 shelf_id(null이면 Board 기본)와 전체 이전/이후 액션을 담는다. 해당 이벤트의 top-level 회원 before/after와 target_user_id는 null이다. 이유는 공통 reason 필드로 제공하고 원본 JSON/계정 비공개 필드를 노출하지 않는다.

## 후속 경계

현재 Canvas 모델/목록 API가 없어 모든 현재 Shelf에는 게시글 참조가 없다. 삭제는 현재 Shelf/정책을 정리하며 기본/마지막 Shelf 보호와 다른 Board/멤버/등급/기본 정책 보존을 검증한다. #8에서 Canvas를 연결하기 전에 (board_id, shelf_id) 복합 FK와 RESTRICT 삭제, 초안/휴지통을 포함한 비어 있지 않음 검사·원자적 이동·권한이 적용된 공개 snapshot 목록/cursor를 함께 추가해야 한다. 이 검증 전에는 콘텐츠가 있는 Shelf 삭제를 지원한다고 설명하지 않는다. Smart Shelf·인기/조회 통계·Canvas/댓글/에셋의 실제 권한 적용·UI는 후속이며 #23 전체는 열린 상태로 유지한다.
