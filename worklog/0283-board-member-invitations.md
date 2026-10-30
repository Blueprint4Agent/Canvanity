# Commit Title

feat: 보드 기존 계정 수동 초대 API를 구현한다

# Changed File Scope

Board 모델/저장소·DI 회원 서비스·공유 권한 가드·라우터/오류, API/인증/실제 PostgreSQL 회귀, 양쪽 OpenAPI·생성 타입, 한국어 도메인 문서. #35, 상위 #22/#1. 제품 UI와 외부 메시지 발송은 제외한다.

# Reason

사용자 요청으로 #33/#34를 main에 병합한 뒤 다음 기존 계정 초대 기능을 진행한다. invite 정책 Board의 운영자가 활성 기존 계정을 현재 기본 등급의 일반 회원으로 등록할 수 있어야 한다. 초대로 운영 역할을 부여하거나 제재/승인 상태를 초기화하지 않는다.

# Design

기준 main `8c835de66ac351d055033335bcf9f1ab26efaeea`, 브랜치 feat/board-member-invitations. POST members는 user_id/expected_revision/reason을 받고 기존 회원 상세/revision 응답을 재사용한다. 현재 active Owner/Admin·active Board·invite 정책을 검사한 뒤 기존 활성 계정을 확인한다. 기존 active 회원은 no-op, pending/suspended/banned는 409다. Board 잠금과 대상 계정의 활성/삭제 경쟁을 검토하고 현재 기본 등급으로 Member를 등록한다. 회원·감사·revision은 기존 models/board.py의 한 트랜잭션에서 저장한다. 서비스는 현재 권한/상태·흐름, 모델은 SQL·세션·ORM 쓰기·DB 오류 정규화를 소유한다.

# Verification Plan

API 계약·Bearer/API key 인증 인벤토리·각 Board 역할/상태·public/private invite 및 open 정책 거부를 확인한다. 현재 기본 등급·역할/상태 유지·계정 없음/비활성·제재 재등록 거부·stale revision/no-op·감사/롤백을 검증한다. 격리 PostgreSQL에서 같은 revision의 등록 경쟁 단일 승자와 계정 활성/삭제 경계를 확인한다. 루트 VERIFY_BASE=8c835de make verify-plan → VERIFY_JOBS=1 VERIFY_BASE=8c835de make verify를 실행한다.

# Impact

기존 회원/등급/감사 테이블을 재사용한다. 이 API는 수락 대기 초대가 아니라 기존 계정의 즉시 수동 등록이다. 이메일/링크 초대·가입 승인·Board 정보 수정/위임/종료·Shelf 정책 편집·UI·운영 배포는 후속이다.

# Loop Alignment

요청→라우터→DI 회원 서비스/공유 가드→모델 Repository/잠금 트랜잭션→응답이다. 권한은 요청마다 현재 데이터로 검사한다. 계약 생성 타입 외 프런트 런타임·상태/UI·실시간·백그라운드 작업은 변경하지 않는다.

# Verification

구현 전 계획을 기록했다. 시작 작업 트리는 깨끗했고 기존 UI stash는 적용하지 않았다. #33은 991f1df, #34는 8c835de의 두 부모 merge commit으로 병합하고 main을 fast-forward했다. 최종 tree가 기존 검증의 fbbaac4와 같아 병합만을 위한 전체 재검증은 생략했다. #34 기준 전환 직후 PR 거버넌스를 fetch보다 먼저 실행해 로컬에 새 base 객체가 없어 한 차례 실패했으며 fetch 후 실제 메타데이터 재검사로 통과했다. 훅은 우회하지 않았다. 초대 구현 시작/완료 시 수동 책임 경계 검토를 수행한다.

대상 API·통합·인증 61개 통과(24.08초). 현재 기본 등급·Member 역할, invite 공개 범위·역할/상태·기존 active no-op·pending/제재 재초대 거부·없음/비활성 계정·stale revision·개인정보 최소화·감사/commit rollback을 확인했다. 인증 인벤토리와 실제 발급 API key 거부도 포함했다.

최종 실제 PostgreSQL 검사 1개 통과(1.14초). 같은 revision 초대 두 요청 중 하나만 성공하고 하나는 409이며 감사 1건·revision 1회 증가를 확인했다. 기존 active 재호출은 no-op이다. 계정 비활성화/삭제 중 대상 조회의 실제 pg_blocking_pids를 관측하고, 계정 변경 commit 이후 초대 404와 회원/감사/revision 불변을 확인했다. 기존 생성·가입·등급 순서/삭제·migration 왕복과 임시 schema 제거도 유지했다. 로그는 `.git/member-invitations/postgres-final.log`다.

루트 VERIFY_BASE=8c835de make verify-plan 이후 VERIFY_JOBS=1 VERIFY_BASE=8c835de make verify 전체 15명령 통과(393.6초). 백엔드 645 통과/PG opt-in 1 skip(위 별도 통과), 프런트 단위 207·브라우저 250·production 18·style-studio 3 및 아키텍처·계약/생성 타입·설정/도구·빌드/패키징 검사 통과. 모델/공유 권한/계약 변경으로 전체 범위를 유지했고 수동 축소하지 않았다. 로그는 `.git/verification-logs/run-7rsgn1ka`, 계획은 `.git/member-invitations/verify-plan.log`다.

완료 수동 검토: 라우터는 DI 회원 서비스의 공개 invite만 호출한다. 회원 서비스/공유 가드는 현재 역할·상태·정책과 expected_revision을 검사하며 DB 쿼리/세션/ORM 쓰기·DB 예외 원문 해석이나 다른 서비스의 비공개 메서드 호출이 없다. 모델은 Board 잠금→대상 User 공유 잠금→회원/감사/revision 저장을 소유한다. 기존 계정 삭제는 users 테이블/행 잠금 뒤 소유 Board를 일반 조회하며 Board 행을 역순으로 잠그지 않음을 확인했다. self join과 수동 초대의 일반 회원 초기값을 모델의 private 생성 메서드로 공유하고 기존 self join 감사 형식은 유지했다. 새 예외는 영어 기본 문구·도메인 enum·공통 응답 빌더를 사용한다. 새 테이블/migration·제품 UI·발송/작업·실시간 변경은 없으므로 별도 화면/성능 측정은 해당하지 않는다.

양쪽 OpenAPI·생성 타입과 한국어 문서를 동기화했다. #31/#32는 병합 완료로 닫고, #35와 상위 #22/#1에서 구현·검증·원격 게시·main 병합을 구분해 추적한다. 이번 초대 기능의 원격 병합/운영 배포는 별도 상태다.
