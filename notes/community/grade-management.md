# Board 회원 등급 설정 API — #32

회원에게 등급을 부여하는 [회원 운영 API](member-administration.md)와 등급 자체의 설정을 구분한다. 뉴커머·피너·큐레이터도 이름을 바꿀 수 있으며 `grade_id`는 유지한다. 운영 역할(owner/admin/moderator/member)은 등급과 독립적이다. 현재 작업은 백엔드·계약이며 UI와 운영 배포는 포함하지 않는다.

## API와 권한

경로는 `/api/v1/boards/{board_id}` 기준이다. 모든 응답에 `Cache-Control: private, no-store`를 적용한다. 변경 요청은 Bearer 인증·`expected_revision`·공백 제거 후 1~500자의 `reason`을 요구한다.

| Method | 경로 | 계약 |
| --- | --- | --- |
| GET | `/grades` | 현재 읽을 수 있는 Board의 `{items, board_revision}`. 최대 20개를 rank 오름차순으로 반환하며 페이지네이션은 없다. 개인정보는 포함하지 않는다. |
| POST | `/grades` | name 1~30자, rank 0~2,147,483,647 정수. 기본값이 아닌 등급을 생성하고 201 `{grade, board_revision}`와 Location을 반환한다. |
| PATCH | `/grades/{grade_id}` | name 또는 `is_default: true` 중 하나 이상. 이름만 바꾸면 회원·정책의 ID 참조는 유지한다. 200 `{grade, board_revision}`. |
| PATCH | `/grades/order` | `grade_ids`에 현재 Board의 모든 등급을 정확히 한 번씩 지정한다. 입력 순서대로 rank 0/10/20/…을 부여하고 200 `{items, board_revision}`를 반환한다. |
| DELETE | `/grades/{grade_id}` | 같은 Board의 다른 `replacement_grade_id`를 필수 지정한다. 회원·Board/Shelf 정책 참조를 이동하고 200 `{items, board_revision}`로 남은 목록을 반환한다. |

조회는 Board 홈과 같은 공개/비공개·현재 멤버 상태 검사를 적용한다. 공개 Board는 익명 조회가 가능하지만 suspended/banned 멤버는 기존 토큰으로도 404다. 비공개는 active 멤버만 조회한다. 변경은 active Board의 현재 active Owner/Admin만 가능하며 Moderator·일반 회원·타 Board 운영진·앱 전역 Admin에게 권한을 부여하지 않는다. archived는 조회만 허용하고 suspended Board는 숨긴다.

PATCH의 필드 생략은 유지, 명시적 null은 422다. 기본 등급 해제만 보내는 `is_default: false`도 거부한다. 새 기본 등급에 `true`를 보내 한 번에 이전한다. rank는 순서 API에서만 바꾼다. 이름은 앞뒤 공백을 제거하고 같은 Board 안에서 대소문자를 구분하는 고유성을 사용한다. 기존 값과 같은 이름·기본값 또는 이미 정규화된 같은 순서는 revision·감사 기록을 증가시키지 않는다. 이 경우에도 현재 권한과 expected_revision 검사는 수행한다.

```json
{
  "expected_revision": 7,
  "reason": "커뮤니티 등급명 정리",
  "name": "새로운 이웃",
  "is_default": true
}
```

기본 등급 변경은 기존 회원의 등급을 일괄 변경하지 않고 이후 가입자에게 적용한다. 순서 변경은 기존 grade_id를 유지하면서 현재 최소 등급 비교 결과를 바꾼다. 예를 들어 게시 기준 등급보다 회원 등급을 위에 배치하면 다음 요청부터 권한이 달라진다. 이것이 운영 역할의 승격을 뜻하지는 않는다.

## 원자성과 감사

변경은 기존 models/board.py의 Board 행 잠금 아래에서 현재 운영 권한과 revision을 재검사한다. 서비스는 정책/오케스트레이션, 모델은 SQL·세션·ORM 변경·commit/rollback·DB 오류 정규화를 담당한다. 새 Repository 파일이나 DB 세션 전달을 추가하지 않는다.

등급은 1~20개이고 기본 등급은 정확히 하나다. 기본값 전환은 이전 기본 플래그를 먼저 flush한 뒤 새 기본값을 지정한다. 순서 변경은 기존/최종 rank와 겹치지 않는 작은 양수 임시 rank로 flush한 다음 최종 rank로 다시 flush한다. 기존 최대 rank에 더하는 방식은 정수 범위 초과가 가능하므로 사용하지 않는다. 즉시 적용되는 유니크 제약을 완화하지 않는다.

삭제는 같은 트랜잭션에서 회원 grade_id와 Board/Shelf 정책의 min_grade_id를 대체 등급으로 이동한다. 기본 등급을 지우면 대체 등급이 기본값이 된다. 마지막 등급 삭제는 409, 자기 자신·다른 Board·존재하지 않는 대체 등급은 422다. 대상 등급 부재/타 Board는 404다. 삭제 시 역할·멤버 제재 상태와 public/staff_only 같은 정책의 나머지 필드는 유지한다.

실제 변경마다 Board revision을 한 번 증가시키고 `grade_created`, `grade_updated`, `grades_reordered`, `grade_deleted` 감사를 같은 트랜잭션에 기록한다. `target_user_id`는 null이다. Owner/Admin의 `/member-audit`에서 `grade_change` 허용 필드로 이전/이후 등급 목록, 대체 ID, 회원·Board/Shelf 정책별 이동 수를 조회한다. 기존 회원 감사의 before/after는 그대로 유지하며 원본 changes JSON을 노출하지 않는다. 실패하면 기본값·rank·참조·revision·감사가 함께 롤백된다.

중복 이름/rank·20개 초과·마지막 등급은 각각 409 도메인 오류로 구분한다. 잘못된 전체 순서는 422다. stale revision은 `BOARD_REVISION_CONFLICT` 409와 current_revision을 반환한다. DB 원문과 제약 이름은 응답하지 않는다. 기존 테이블/제약을 재사용하므로 이 작업의 새 migration은 없다.

## 기본 예외 메시지 검토

Board의 enum → ServiceException → 공통 응답 빌더/전역 핸들러 구성은 Auth/APIKey 등과 같다. Board에만 한국어였던 default_message는 기존 도메인과 동일하게 영어 기본 메시지로 정리했다. 전역 핸들러는 Accept-Language로 번역하지 않는다. 프런트는 `detail.error` 코드에 연결된 한국어/영어 i18n을 사용하며 에러 코드·HTTP 상태·details 모양은 유지한다. 이번 작업에 UI 실행 코드는 추가하지 않는다.

## 검증과 후속

API 계약·실제 저장 통합 검사로 읽기 경계·운영 역할·입력 계약·이름/ID 유지·이후 가입자 기본값·최소 등급 즉시 반영·참조 이동·no-op/stale revision·감사/롤백을 확인한다. 별도 격리 PostgreSQL 검사에서 기본/rank 유니크, INTEGER 최대 rank를 포함한 재정렬, 경쟁 변경 단일 승자, 참조 대체와 rollback 및 migration 왕복을 확인한다. 최종 결과는 worklog/0282-board-grade-management.md와 [#32](https://github.com/Blueprint4Agent/Canvanity/issues/32)에서 추적한다.

자동 승급·활동 집계·사용자 정의 운영 역할·초대·위임·Board 종료·Shelf 정책 편집과 UI는 각 후속 작업에서 진행한다.
