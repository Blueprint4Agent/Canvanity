# Board 기본 정보·공개 정책·보관/복원 — #37

PATCH /api/v1/boards/{board_id}는 expected_revision·reason과 변경 필드를 받는다. Bearer 전용이며 현재 active Owner/Admin만 관리한다. visibility/status 제공은 Owner 전용이므로 같은 값을 포함한 Admin 혼합 요청도 전체 거부한다.

| 필드 | 입력 | 권한 |
| --- | --- | --- |
| name | 공백 제거 후 1~80자 | Owner/Admin |
| description | 최대 2,000자, 빈 문자열로 지우기 | Owner/Admin |
| rules | 최대 10,000자, 빈 문자열로 지우기 | Owner/Admin |
| interest_ids | 활성 공식 Interest 최대 3개, 고유 ID·순서 유지, []로 지우기 | Owner/Admin |
| join_policy | open/invite, 최종 private/open 거부 | Owner/Admin |
| visibility | public/private | Owner |
| status | active/archived, suspended 설정/해제 미지원 | Owner |

reason은 공백 제거 후 1~500자다. 생략은 유지, 명시적 null·빈 변경·slug/owner_id/에셋 등 추가 필드는 422다. 같은 값은 no-op이지만 권한/revision 검사는 수행한다. 성공은 200 {board, rules, board_revision}와 Cache-Control: private, no-store다. board는 기존 BoardSummary이며 revision도 동일하다.

public→private는 이미 invite여도 같은 요청에 join_policy:invite를 명시한다. 기존 회원·등급·Shelf·홈과 정책을 보존한다. public 읽기 정책도 private Board에서는 active 멤버만 허용하며 pending/제재 상태는 우회하지 않는다. 비회원은 상세·slug·목록에서 private Board를 읽지 못한다. private→public은 Owner만 허용하며 public 정책은 다시 익명 읽기에 적용될 수 있지만 members/최소 등급/staff_only 정책은 자동 개방하지 않는다. 공개 범위는 상위 경계이며 정책을 덮어쓰지 않는다.

Owner는 status:archived로 보관하고 status:active로 명시적으로 복원한다. archived 정보 수정은 복원과 함께 요청해야 한다. status:archived만 반복하면 no-op이고 Admin 복원은 거부한다. 기존 데이터/읽기와 본인 탈퇴·빈 Board 삭제 계약은 유지한다. suspended Board는 운영자에게도 404이고 이 API로 해제하지 않는다.

공식 활성 Interest만 새로 선택하고 프로필 관심사·자유 태그는 바꾸지 않는다. 생략한 기존 비활성 Interest 연결은 DB에 보존하되 일반 응답은 기존 GET처럼 활성 ID만 표시한다. 명시 목록은 전체 연결을 대체하며 다른 Board의 연결은 유지한다. 감사는 실제 저장된 이전/이후 연결을 남긴다.

서비스는 정책/흐름, 기존 models/board.py는 SQL·세션·ORM 쓰기·오류 정규화를 소유한다. Board 잠금 안에서 현재 권한/revision을 확인하고 설정·연결·revision 1회 증가·board_updated 감사를 같은 트랜잭션에 저장한다. 실패하면 함께 롤백한다. 새 테이블/migration·Repository 파일은 없다.

Owner/Admin의 member-audit는 board_change DTO로 이전/이후 이름·소개·규칙·관심사·공개/가입 정책·상태만 반환한다. 이 이벤트의 회원 before/after는 null이며 기존 회원/등급 감사는 유지한다. 원본 changes JSON·계정 이메일/인증 정보는 노출하지 않는다. stale revision은 BOARD_REVISION_CONFLICT 409, 잘못된 공개/가입 조합은 BOARD_INVALID_SETTINGS 422, 비활성/없는 관심사는 BOARD_INVALID_INTEREST 422다. 예외 기본 문구는 영어, UI는 코드 기반 번역이다.

검증은 역할/제공 필드·공개 범위/보관·관심사·혼합 요청 원자성·no-op/revision·감사/rollback과 실제 PostgreSQL 동시 변경 단일 승자를 포함한다. worklog/0284-board-settings.md와 #37에서 추적한다. 선행 초안 PR #36 기준의 별도 변경이며 UI·공개 전환 영향 안내·소유권 위임·영구 삭제/파일 정리 outbox·에셋·Shelf 정책 편집·운영 배포는 후속이다.
