# Board 구독과 본인 구독 피드

상위 [#26](https://github.com/Blueprint4Agent/Canvanity/issues/26)의 독립 단위 [#65](https://github.com/Blueprint4Agent/Canvanity/issues/65)다. 가입은 권한, 구독은 피드 선택이며 두 관계를 자동으로 맞추지 않는다. 제품 UI·알림·추천은 별도다.

## 사용자 흐름과 계약

- `GET /boards/{board_id}/subscription`: 현재 읽을 수 있는 Board의 본인 `{subscribed}`를 반환한다.
- `PUT` 같은 경로: active Board를 구독한다. 공개 Board는 비회원도 가능하며 private은 현재 활성 회원만 가능하다. 이미 구독 중이면 행/시각을 바꾸지 않는다.
- `DELETE` 같은 경로: 본인 구독을 취소한다. 없는 관계도 성공하며 현재 읽을 수 있는 archived Board에서도 취소할 수 있다.
- `GET /me/subscriptions/canvases`: 현재 구독한 Board 중 읽을 수 있는 게시본을 기존 [공개 Feed](canvas-feed.md)의 items/next_cursor로 반환한다. `limit`, `cursor`, `sort=latest`, 공식 Interest slug와 게시 Tag UUID 필터를 받는다.

모두 세션 전용이고 응답은 private,no-store다. 구독자 명단/다른 사람의 상태는 제공하지 않는다. API Key는 사용할 수 없다. 등록/취소는 가입·탈퇴·등급·Board revision을 바꾸지 않고, 가입·탈퇴도 구독을 바꾸지 않는다.

## 현재 권한과 일관성

구독 상태/변경은 현재 Board/회원 제재·private 자격과 활성 계정을 검사한다. 등록은 active Board만 허용하며 suspended/차단/접근 불가는404다. 읽기는 가능하나 보관 Board를 등록하려 하면403이다. private 전환이나 탈퇴 뒤 접근할 수 없어진 관계는 보존하되 상태/피드에서 숨긴다. 권한이 다시 생기면 같은 관계를 사용한다.

구독 피드는 가입/구독을 권한으로 간주하지 않고 현재 Board/Shelf/회원 정책·Canvas/publication visibility·게시 상태를 매 페이지 적용한다. 구독 취소·정책/제재·게시 취소 후 다음 페이지에도 같은 정책을 적용한다. cursor는 사용자/경로/필터에 결합한다. 페이지 크기는 바꿀 수 있으며 구독 피드와 일반 Plaza cursor는 교환할 수 없다. 구독 관계는 공개 header/태그와 같은 SQL statement의 EXISTS로 필터링하므로 본문 JSONB·N+1 조회를 추가하지 않는다.

## 저장과 수명주기

0033은 `(board_id,user_id)` 복합 PK와 사용자 조회 인덱스를 추가한다. 두 FK의 CASCADE로 Board/계정 영구삭제 시 관계를 제거한다. 등록/취소는 Board 배타→현재 User 공유 잠금으로 현재 정책/계정 변경과 직렬화한다. 같은 요청 반복과 동시 등록은 하나의 관계만 남긴다. 실패/commit 오류는 저장소가 Board 도메인503으로 변환하고 부분 상태를 반환하지 않는다. 관계가 남은 downgrade는 거부한다.

## 검증과 상태

API/세션·필터, 실제 HTTP/SQLite의 가입 독립성·멱등/no-op·private 전환/제재·보관/취소·게시 취소·rollback과 격리 PostgreSQL의 동시 등록·migration/자료 보존·페이지 간 제재·사용자 cursor·계정 삭제를 검증한다. 실제 전체 검증/ready PR/main 반영은 [worklog0303](../../worklog/0303-board-subscriptions.md)과 이슈/PR을 따른다. 운영 DB migration/배포는 별도다.
