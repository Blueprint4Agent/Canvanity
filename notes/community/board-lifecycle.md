# Board 소유권 위임·종료 — #39

POST /api/v1/boards/{board_id}/ownership-transfer는 expected_revision, target_user_id(JSON 정수 1~2,147,483,647), 공백 제거 후 1~500자의 reason을 받는다. Bearer 전용이고 현재 owner_id와 일치하는 active Owner만 가능하다. Board active/archived에서 허용하고 suspended는 404다. 같은 Board의 다른 active 회원/활성 계정만 대상으로 하며 자기 자신·다른 Board/비회원·pending/제재·비활성/없는 계정은 BOARD_INVALID_OWNERSHIP_TARGET 422다. Admin·Moderator·일반 회원·앱 전역 Admin은 소유권을 얻지 않는다.

성공은 200 {board_id, previous_owner_id, owner_id, board_revision}와 Cache-Control: private, no-store다. 기존 Owner는 Admin, 대상은 Owner가 되고 활동 등급·상태·가입 시각과 전역 계정 역할은 유지한다. 새 Owner 권한은 다음 요청부터 적용되며 구 Owner는 Owner 전용 작업을 못 한다. 보유 Board가 없어지면 구 Owner는 기존 계정 삭제 소유 검사를 통과할 수 있다. 새 Owner 계정 삭제는 다시 BOARD_OWNERSHIP_REQUIRED로 보호한다.

기존 models/board.py의 Board 잠금 아래 현재 역할/revision을 검사하고 대상 User FOR SHARE로 활성 확인과 계정 삭제를 직렬화한다. 즉시 부분 유니크를 지키도록 기존 Owner→Admin을 먼저 flush한 뒤 새 Owner·owner_id·revision 1회 증가·ownership_transferred 감사를 저장한다. 실패하면 모두 롤백한다. 같은 Owner가 동시에 위임하면 하나만 성공하고 다른 요청은 현재 역할이 Admin으로 바뀌어 403이다. Owner가 여전히 유효한 stale revision은 409다.

member-audit의 ownership_change는 이전/이후 owner_id와 두 회원의 user_id/role/status/grade_id만 반환한다. top-level 회원 before/after는 null이며 원본 JSON/계정 비공개 필드는 노출하지 않는다. 이 이벤트의 수행자는 구 Owner, 대상은 새 Owner다.

DELETE /api/v1/boards/{board_id}는 기존 expected_revision/confirm_slug 계약과 204 응답을 유지한다. archived에서는 다른 회원이 있어도 현재 Owner가 현재 구현된 Board·멤버·등급·관심사 연결·정책·Shelf·홈·감사를 원자적으로 삭제한다. active는 기존 빈 Board 되돌리기(Owner 한 명)만 허용하고 다른 회원이 있으면 409다. 확인 문자열 오류 422, stale revision 409, 현재 Owner가 아니면 403(숨겨진 객체는 404), suspended는 404다. 기존 DELETE operation ID도 유지한다.

Board 삭제는 User/전역 Interest/다른 Board를 삭제하지 않는다. 현재 Board에는 avatar/cover/Canvas/asset 파일 참조가 없어 물리 삭제할 Board 소유 파일이 없다. User 프로필 사진은 보존하고 prefix/레이아웃 JSON으로 파일 소유권을 추측하지 않는다. 기존 프로필 정리의 무보장 동작을 새 Board 파일 정리 보장으로 설명하지 않는다.

#6/#8에서 실제 에셋/게시글을 연결하기 전에 Board 삭제 트랜잭션에 asset_deletion_outbox와 공유 draft/publication 참조 검사·원래 저장소 위치·재시도/운영 재처리를 통합해야 한다. outbox는 부모 Board 삭제 후에도 남아야 하며 그때 하위 Canvas/댓글/반응 등 전체 삭제와 active 빈 Board 판정도 확장한다. 현재 사용하지 않는 에셋/outbox/worker는 추가하지 않는다. #22 전체와 파일 수명주기는 미완료다.

검증은 역할/상태/현재 권한·등급/가입 시각 보존·계정 삭제 소유 경계·동시 위임 단일 승자·Owner 유니크·감사/rollback·보관 삭제·active 빈 Board 호환성과 다른 Board/계정/프로필 파일 보존을 포함한다. 실제 PostgreSQL은 격리 schema에서 위임/삭제·제약/rollback·migration 왕복을 검증한다. worklog/0285-board-ownership-lifecycle.md와 #39에서 구현·검증·게시·main 병합을 구분한다. 기준은 선행 초안 PR #38이며 UI/운영 배포는 포함하지 않는다.
