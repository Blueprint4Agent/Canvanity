# Board 기존 계정 수동 초대 — #35

`POST /api/v1/boards/{board_id}/members`는 invite 정책 Board의 현재 active Owner/Admin이 기존 활성 계정을 즉시 등록하는 API다. public/invite와 private/invite를 지원하며 public/open은 기존 self join을 사용한다. 이메일·링크 발송이나 수락 대기/가입 승인 흐름은 후속이다. 제품 UI와 운영 배포는 포함하지 않는다.

```json
{
  "user_id": 42,
  "expected_revision": 7,
  "reason": "프로젝트 참여 회원 등록"
}
```

Bearer 인증을 요구한다. user_id는 1~2,147,483,647의 JSON 정수, expected_revision은 0 이상, reason은 공백 제거 후 1~500자다. 이메일·role/status/grade_id 등 추가 필드는 422다. Moderator·일반 회원·타 Board 운영진·앱 전역 Admin은 Board 운영 권한을 얻지 않는다. archived Board는 변경 403, suspended 및 읽기 권한 없는 private Board는 404다. 현재 Actor 멤버 상태도 매번 검사한다.

새 회원은 요청 시점 기본 등급의 active Member로 등록한다. Curator를 기본값으로 설정하거나 초대 대상의 앱 역할이 Admin이어도 Board 운영 역할은 member다. 이미 active 회원이면 기존 역할·등급·상태·joined_at을 그대로 반환하며 revision/감사를 늘리지 않는다. 이 경우에도 최신 expected_revision은 필요하다. pending/suspended/banned 회원은 BOARD_INVITATION_CONFLICT 409로 거부하며 상태 변경은 별도 회원 운영 PATCH를 사용한다. 초대로 승격·제재 해제·승인 처리를 수행하지 않는다.

성공은 200 `{member, board_revision}`와 `Cache-Control: private, no-store`다. 기존 회원 상세 DTO의 공개 프로필·역할·상태·등급·가입 시각만 반환하고 이메일/인증 정보는 포함하지 않는다. 대상 계정이 없거나 비활성이면 BOARD_INVITEE_NOT_FOUND 404, stale revision은 BOARD_REVISION_CONFLICT 409와 current_revision이다.

요청→라우터→DI BoardMembershipService/BoardPermissionService→기존 models/board.py Repository를 따른다. 서비스는 흐름·권한을 판단하고, SQL·세션·ORM 쓰기·DB 오류 정규화는 모델에 둔다. Board 행 잠금 아래에서 권한·revision을 확인하고 대상 계정에 FOR SHARE를 적용해 활성 확인부터 commit까지 비활성화/삭제를 직렬화한다. 기존 계정 삭제는 User 잠금 뒤 소유 Board를 일반 조회하고 멤버 삭제는 FK cascade하므로, 해당 흐름에 역방향 Board 행 잠금을 추가하지 않는다. 공유 잠금 때문에 같은 대상의 이름/계정 수정도 짧은 초대 트랜잭션이 끝날 때까지 기다릴 수 있다.

회원 등록·revision 1회 증가·member_invited 감사(수행 운영자/대상/이전 없음/이후 role/status/grade_id/reason)는 같은 트랜잭션에서 commit한다. 실패하면 함께 롤백한다. 감사는 기존 Owner/Admin의 member-audit에서 조회한다. 기존 self join의 member_joined 이벤트와 기본값은 유지한다. 새 테이블이나 migration은 없다.

수용 검증은 API/인증 계약, 역할/상태 행렬, 현재 기본 등급, no-op/stale revision, 개인정보·제재 경계, commit 실패 롤백이다. 실제 PostgreSQL에서는 동일 revision 초대의 단일 승자/409·감사 1건과 pg_blocking_pids로 계정 비활성화/삭제 잠금 대기를 관측한 뒤 404·회원/감사/revision 불변을 확인한다. 결과는 worklog/0283-board-member-invitations.md와 [#35](https://github.com/Blueprint4Agent/Canvanity/issues/35)에 기록한다.
