# Board 회원 운영 API

추적: [#31](https://github.com/Blueprint4Agent/Canvanity/issues/31) · [회원 권한 정책](membership-policy.md) · [API 계약](api-design.md)

이 단계는 백엔드 API와 계약만 구현한다. UI·등급 이름/순서 정의 편집·초대·소유권 위임은 포함하지 않는다. 등급 정의 관리는 [#32](https://github.com/Blueprint4Agent/Canvanity/issues/32)에서 이어간다.

## 회원 목록

`GET /api/v1/boards/{board_id}/members`는 Bearer 세션과 해당 Board의 현재 운영 역할을 요구한다. `limit`은 1~100(기본 20), `q`는 이름/handle의 문자 그대로 검색(최대 200자), `role`/`status`는 선택 필터다. `cursor`는 최대 2,048자이며 사용자·Board·조회 범위·필터와 결합한다.

Owner/Admin 응답은 `scope=management`이고 회원의 user_id/name/handle/role/status/grade_id/grade_name/grade_rank/joined_at을 제공한다. Moderator 응답은 `scope=moderation`이고 제재 가능한 active 일반 Member만 조회하며 항목 필드는 user_id/name/handle뿐이다. 일반 회원은 403, private Board 비회원과 제재된 회원은 404다. 계정 전역 Admin이나 다른 Board 운영진에게 이 권한을 주지 않는다. 이메일·인증·토큰·계정 전역 역할을 반환하지 않는다.

페이지는 `{scope,items,next_cursor,board_revision}`이다. 가입 시각과 user_id 내림차순으로 정렬하며 total은 제공하지 않는다. 현재 권한/필터를 매 페이지 다시 적용하고 권한 변경 중의 완전한 snapshot pagination은 보장하지 않는다.

## 회원 변경

`PATCH /api/v1/boards/{board_id}/members/{user_id}`:

```json
{
  "expected_revision": 6,
  "reason": "프로젝트 참여에 따른 수동 등급 변경",
  "grade_id": "00000000-0000-4000-8000-000000000010"
}
```

`role`, `status`, `grade_id` 중 하나 이상을 지정한다. 명시적 null과 알려지지 않은 필드는 422다. `reason`은 공백 제거 후 1~500자, expected_revision은 현재 Board revision이다. `role=owner`와 `status=pending`은 이 경로에서 받지 않는다.

- Owner만 Admin을 임명/해제한다. Owner/Admin은 일반 Member/Moderator의 등급과 Moderator 역할을 변경한다. Admin은 Owner/Admin·본인을 임의 변경하지 못한다.
- Moderator는 현재 active 일반 Member의 status를 suspended/banned로 바꾸는 것만 가능하다. role/grade_id를 같이 보내면 값이 같아도 요청 전체를 거부한다. 제재 해제는 Owner/Admin이 수행한다.
- 본인/Owner와 pending 대상의 변경은 거부한다. 소유권 이전·가입 승인 워크플로는 후속이다.
- 운영 역할을 새로 지정하는 요청은 최종 상태가 active여야 한다. 이미 운영자인 회원을 Owner가 정지/차단하는 것은 가능하며 역할이 있어도 제재 상태를 우회하지 못한다.
- grade_id는 같은 Board의 기존 등급만 허용한다. 등급을 높여도 운영 역할을 부여하지 않는다.

모든 제공 필드의 권한·최종 상태·등급 소속을 검사한 뒤 모델의 같은 Board 잠금 트랜잭션에서 저장한다. 하나라도 금지이면 변경·감사·revision 모두 반영하지 않는다. 실제 값이 같은 변경은 감사/revision을 추가하지 않는다. 오래된 revision은 409 BOARD_REVISION_CONFLICT다. 응답은 `{member,board_revision}`이고 현재 토큰의 이후 요청은 변경된 회원 상태·등급·역할로 평가한다.

## 감사 조회

`GET /api/v1/boards/{board_id}/member-audit?since=...&until=...`는 Owner/Admin만 허용한다. 시작/종료 시각은 시간대가 있는 값을 필수로 지정하고 UTC로 정규화한다. `since < until`, 기간은 최대 180일이다. 이는 조회창 제한이며 데이터 보존/삭제 기간을 뜻하지 않는다.

선택 필터는 target_user_id, limit(1~100), cursor다. 감사 시각·UUID 내림차순의 `{items,next_cursor,board_revision}`을 반환한다. 항목은 id/actor_user_id/target_user_id/action/before/after/reason/created_at이며 before/after는 role/status/grade_id만 제공한다. 과거 생성/가입/탈퇴 기록도 이 형태로 변환하며 원본 changes JSON을 그대로 노출하지 않는다. 삭제된 사용자 ID는 nullable이다. 조회 기간과 대상 필터가 바뀐 cursor는 422다.

## 저장과 검증

라우터는 BoardMembershipService를 주입받고 서비스는 BoardPermissionService와 models/board.py의 BoardRepository를 사용한다. 쿼리·세션·잠금·ORM 저장 필드 변경·감사 저장·flush/commit과 DB 오류 변환은 모두 같은 모델 파일의 Repository/BoardTransaction 안에 있다.

0025_board_member_indexes는 기존 테이블에 `(board_id,joined_at,user_id)`와 `(board_id,created_at,id)` 조회 인덱스만 추가한다. 배포 시 기존 migration 경로로 적용한다. 회원 데이터/스키마 필드는 바꾸지 않는다. 실제 PostgreSQL에서 동시 변경의 단일 승자·stale revision·감사 원자성·타 Board 등급 거부와 migration 왕복을 검증한다.
