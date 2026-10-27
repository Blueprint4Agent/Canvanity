# 멤버십·회원 등급·권한 정책

[도메인](domain-model.md) · [API](api-design.md)

## 네 가지 독립 축

| 축     | 값·책임                                                                 |
| ------ | ----------------------------------------------------------------------- |
| role   | owner/admin/moderator/member. 운영 책임이며 앱 전역 UserRole과 별개     |
| grade  | Board별 Newcomer/Pinner/Curator 등. 운영자가 이름·순위·기본 등급을 관리 |
| status | pending/active/suspended/banned. 가입과 제재 상태                       |
| policy | 액션별 audience/min_grade_id/staff_bypass. Board 기본값과 Shelf 재정의  |

`board_member_grades.rank`는 큰 값이 높은 등급이다. 기본값은 뉴커머(Newcomer) 0, 피너(Pinner) 10, 큐레이터(Curator) 20이다. 등급 이름이 같아도 Board 간 동일 권한을 의미하지 않는다. Owner에게도 grade_id가 있지만 등급을 높여 운영 권한을 주지 않는다.

MVP는 public/open 또는 private/invite Board를 지원한다. private/open은 가입 즉시 비공개 자료를 열람하는 모순을 피하려고 422로 거부한다. private/invite는 Owner가 존재하는 사용자 ID를 직접 등록하는 수동 초대만 제공한다. 사용자 지정 이메일 발송·초대 URL/토큰·승인 워크플로는 후속이다. private Board의 join 요청은 403으로 거부한다. approval 입력도 422다.

## Board별 변경 가능 범위

기본 등급은 Newcomer(뉴커머, rank 0) → Pinner(피너, 10) → Curator(큐레이터, 20)다. Board 운영자는 등급 이름·순서·기본 등급과 Shelf별 읽기/글쓰기/댓글/좋아요 정책을 변경할 수 있다. 이름 변경은 표시명만 갱신하고 grade_id 및 기존 회원/정책 참조를 유지한다. rank 순서를 바꾸면 최소 등급 비교 결과가 달라지므로 정책 영향 미리보기와 명시적 저장을 제공한다.

회원에게 Owner/Admin/Moderator/Member 운영 역할을 지정·해제하는 것은 지원한다. 역할별 세부 운영 권한표는 서비스가 정한 값이며 사용자 정의 역할·체크박스식 운영 권한 편집은 후속 범위다. Curator 등급이 되어도 회원 관리 권한이 생기지 않는다.

## 기본 액션 정책

| action         | 공개 Board 기본                           | 비공개 Board 기본                       | Shelf 재정의 |
| -------------- | ----------------------------------------- | --------------------------------------- | ------------ |
| read_canvas    | public, 최소 등급 없음, staff_bypass=true | members, 뉴커머 이상, staff_bypass=true | 가능         |
| create_canvas  | members, 피너 이상, staff_bypass=true     | 동일                                    | 가능         |
| create_comment | members, 뉴커머 이상, staff_bypass=true   | 동일                                    | 가능         |
| react          | members, 뉴커머 이상, staff_bypass=true   | 동일                                    | 가능         |

여기서 public은 **Board가 public이고, 게시글 visibility도 public이며, published snapshot이 있을 때** 비회원 열람을 허용한다. Board가 private이거나 Canvas visibility=members면 active 멤버만 가능하다. 정책에서 public을 선택해도 상위 private 경계를 넓히지 못한다. create/react 등 인증이 필요한 액션은 audience=public을 허용하지 않는다.

공지 Shelf는 create_canvas/create_comment를 운영 역할만 허용한다. 정책은 `staff_only=true` 선택지를 추가하여 명시하며 이때 min_grade_id는 null이고 audience=members다. 일반 Shelf는 Board 정책을 상속한다. 직렬화 스키마는 다음 두 형태만 허용한다.

```json
{
    "audience": "members",
    "min_grade_id": "00000000-0000-4000-8000-000000000010",
    "staff_only": false,
    "staff_bypass": true
}
```

```json
{
    "audience": "members",
    "min_grade_id": null,
    "staff_only": true,
    "staff_bypass": false
}
```

public 읽기 정책은 min_grade_id=null, staff_only=false다. `inherit`는 Shelf 정책 행 부재이며 PUT 요청에서 해당 액션에 null을 보내 삭제한다. Board 기본 정책에는 null/상속을 허용하지 않는다. staff_only 필드와 CHECK는 도메인 표의 policy 테이블에도 적용한다.

## 평가 순서와 변경 경쟁

1. 인증된 계정이 비활성이면 거부한다. 비회원 public 읽기 여부는 별도 판단한다.
2. Board suspended는 운영 역할에도 거부한다. archived는 열람만 가능하다.
3. 해당 Board 멤버 suspended/banned는 public Board 열람도 거부한다. pending은 멤버 전용 기능을 사용할 수 없고 public 읽기만 가능하다.
4. Canvas trashed/archived/draft는 작성자의 전용 조회 경로만 허용한다. 운영자도 타인의 비공개 초안 원문을 읽지 못한다. 게시글 visibility와 Board private 경계는 등급보다 우선한다.
5. Shelf 정책을 조회하고 해당 액션 행이 없으면 Board 기본 정책을 쓴다. 인증/활성 멤버 조건을 먼저 만족해야 한다.
6. staff_only는 owner/admin/moderator만 허용한다. staff_bypass=true면 그 운영 역할은 최소 등급만 우회한다. 일반 회원은 현재 rank가 기준 rank 이상인지 판단한다.
7. 작성·수정·게시 액션은 작성자 여부와 현재 create_canvas 정책을 모두 검사한다. 강등/차단 후 열린 편집기의 저장도 거부한다. 자기 초안의 읽기·휴지통 이동은 낮은 등급에도 허용하되 banned/suspended·Board 정지이면 금지한다.
8. metadata 수정 필드는 별도로 allowlist를 적용한다. 운영자에게 허용된 moderation은 타인 공개 게시물 숨김/휴지통이며 본문 편집이 아니다.

권한 검사는 모든 요청에서 현재 DB 멤버·등급·정책을 읽는다. JWT에 grade/rank/capabilities를 권한 원본으로 넣지 않는다. 변경 API는 Board 행을 FOR UPDATE로 잠그고 권한을 재검사한다. 권한 변경도 같은 잠금을 사용하여 변경 commit 이후 시작한 쓰기가 이전 권한으로 commit하지 않게 한다. 잠금 전에 시작된 public 읽기는 기존 요청을 완료할 수 있으며 응답으로 이미 전달된 정보의 회수는 보장하지 않는다.

규모가 커지면 Board 잠금은 병목이 될 수 있다. 초기에는 짧은 DB 트랜잭션으로 제한하고 파일 I/O를 밖에서 수행한다. 정책 버전 기반 세분화는 측정 후 변경한다. 권한 응답은 `Cache-Control: private, no-store`, 위젯/검색/에셋도 동일하다. 후속 캐시를 추가하면 정책 버전/멤버 버전·사용자·Board를 키에 포함하고 commit 후 무효화한다.

## 역할별 운영 권한

| 액션                         | Owner    | Admin | Moderator               | Member        |
| ---------------------------- | -------- | ----- | ----------------------- | ------------- |
| Board 소개·규칙·공식 홈 수정 | 허용     | 허용  | 거부                    | 거부          |
| Shelf·정책·등급 정의/정렬    | 허용     | 허용  | 거부                    | 거부          |
| 일반 회원 수동 승급/강등     | 허용     | 허용  | 거부                    | 거부          |
| 일반 회원 제재               | 허용     | 허용  | 허용                    | 거부          |
| Admin 임명/해제              | 허용     | 거부  | 거부                    | 거부          |
| Moderator 임명/해제          | 허용     | 허용  | 거부                    | 거부          |
| Owner 변경/마지막 Owner 탈퇴 | MVP 거부 | 거부  | 거부                    | 거부          |
| 멤버 전체 목록·감사 기록     | 허용     | 허용  | 공개 프로필/제재 대상만 | 본인 멤버십만 |
| 타인 공개글 moderation       | 허용     | 허용  | 허용                    | 거부          |
| 타인 초안 열람/본문 수정     | 거부     | 거부  | 거부                    | 거부          |

Admin은 Owner/Admin 본인의 등급·역할·상태를 임의 변경하지 못하고 일반 Member/Moderator만 관리한다. Moderator는 active 일반 Member에 대한 suspended/banned만 변경하며 다른 운영자를 제재하지 못한다. Owner 본인의 active/owner 상태는 변경 불가다. 등급을 수정해도 이 운영 위계는 변하지 않는다. 본인 역할/상태 변경은 탈퇴 경로를 제외하고 거부한다.

Owner 이전은 별도 ownership-transfer에서만 허용한다. 대상은 같은 Board의 active 멤버여야 하며 기존 Owner는 Admin으로 변경된다. sole Owner도 Board 보관→confirm_slug를 통한 영구 삭제로 종료할 수 있다. Owner 이전/Board 삭제/계정 삭제 경로와 파일 정리를 #22/#6 출시 전에 함께 검증한다.

members PATCH는 role/status/grade_id를 한 번에 받을 수 있으나 **제공된 모든 필드의 권한과 최종 상태**를 검사하고 하나라도 금지면 전부 거부한다. 필드 일부만 성공시키지 않는다. 이유(reason) 1~500자와 expected_revision을 필수로 받고 변경 감사 기록에 남긴다.

## 구체적 허용·거부 행렬

조건: public Board A, 일반 Shelf Q는 read 뉴커머/게시글 피너/댓글 피너, 공개글 P와 작성자 U의 초안 D. Board B는 private. staff_bypass=true다.

| 요청자·조건            | Q 목록/P 본문       | 새 글·댓글 | U의 D 조회/수정                | 공식 홈 PUT |
| ---------------------- | ------------------- | ---------- | ------------------------------ | ----------- |
| 비회원                 | 404(멤버 전용 읽기) | 401        | 404                            | 401         |
| A의 뉴커머             | 허용                | 403        | U 본인이면 조회 가능·저장 거부 | 403         |
| A의 피너/큐레이터      | 허용                | 허용       | U 본인이면 허용, 타인 404      | 403         |
| A의 Moderator 뉴커머   | 허용                | 허용       | 타인 404                       | 403         |
| A의 Admin/Owner 뉴커머 | 허용                | 허용       | 타인 404                       | 허용        |
| A의 banned(높은 등급)  | 404                 | 404        | 404                            | 404         |
| B의 Admin, A는 비회원  | 404                 | 403        | 404                            | 403         |

추가 시나리오:

- 뉴커머 → 피너으로 수동 승급 후 POST 가능, 피너 → 뉴커머 강등 후 기존 문서 PUT 403.
- Board B grade_id를 A 멤버/정책에 지정하면 API 422 및 DB FK 거부.
- active→suspended 후 과거 토큰으로 요청하면 거부. 기존 댓글/공개글은 제재만으로 자동 삭제하지 않는다.
- Q 읽기 최소 등급을 큐레이터로 바꾸면 피너 회원의 목록·검색·미리보기·에셋도 404. 공개글 수·Tag 연결 통계에서 제한 항목을 제외한다.
- Admin이 Owner로 자기 승격하거나 Owner를 차단하는 요청은 403. 마지막 Owner 탈퇴는 409.
- 공지 staff_only 정책에서는 큐레이터 Member도 글쓰기/댓글 거부. 운영자도 차단 상태면 거부.

## 자동 승급 확장

수동 승급은 가입 즉시 사용할 수 있다. 자동 승급은 #26 활동 집계 후 `board_grade_rules`와 평가 서비스를 추가한다. 허용 지표는 가입 경과일·유효 방문일·공개글/댓글 수처럼 서버가 집계한 값으로 한정하고 임의 SQL/스크립트는 받지 않는다. 수동 강등 보호/자동 평가 제외 플래그, 중복 이벤트, 삭제·취소 차감, 평가 버전·멱등키를 별도 설계한다. 기본 rank 자체에 활동량을 저장하지 않는다.

## 검증 근거와 구현 경계

행렬은 다음 구현의 수용 기준이다. 이번 PostgreSQL probe는 등급/소속 FK·기본 등급 유니크·revision CAS 등 DB 의미론을 확인하며 **제품 서버 권한 평가기가 구현됐음을 의미하지 않는다**. 구현 시 행렬을 서비스 단위+API 통합 fixture로 옮기고 실제 계정 승급/강등 브라우저 흐름을 검증한다.

[OWASP 객체 권한](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/)과 [속성 권한](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/)에 따라 ID 소속·액션과 수정 필드를 함께 검사한다.
