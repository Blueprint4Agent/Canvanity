# Commit Title

feat: 보드 기본 정보와 공개 정책 및 보관 설정을 구현한다

# Changed File Scope

Board 모델/저장소·DI BoardService·공유 권한 가드·라우터/오류, API/인증/실제 PostgreSQL 회귀, 양쪽 OpenAPI·생성 타입, 한국어 커뮤니티 문서. #37, 상위 #22/#1. 제품 UI는 제외한다.

# Reason

Board 개설 이후 운영자가 소개·규칙·관심사·가입 정책을 관리하고 Owner가 공개 범위·보관/복원을 제어할 수 있어야 한다. 기존 멤버와 명시적 콘텐츠 정책을 보존하면서 현재 역할/상태로 모든 제공 필드를 검사한다.

# Design

기준 fd28a09546aefb7b5df6488b7dba1488a3131a7d, 브랜치 feat/board-settings. 선행 초안 PR #36이 main 미병합이므로 해당 브랜치를 기준으로 차이를 분리한다. PATCH는 expected_revision/reason과 이름·소개·규칙·공식 관심사·visibility/join_policy/status만 받는다. Owner/Admin 기본 편집, visibility/status는 Owner 전용이며 archived 정보 수정은 명시적 복원에만 허용한다. private/open과 public→private invite 명시 누락을 거부한다. 기존 public 읽기 정책은 Board가 private일 때 active 멤버 경계로 제한하며 members 정책을 공개 전환으로 자동 개방하지 않는다. DB 변경·관심사 연결·revision·보드 설정 감사는 기존 models/board.py의 Board 잠금 트랜잭션 안에서 저장한다. 기존 회원 감사에 보드 설정용 허용 DTO를 추가한다.

# Verification Plan

PATCH 입력/인증/역할·제공 필드 행렬, 관심사 활성/개수/고유성/순서·지우기, 공개 범위와 기존 멤버/정책 보존, join/invite 정책 즉시 반영, archived/active 및 suspended 경계, no-op/stale revision·감사/rollback을 검증한다. 실제 PostgreSQL의 동시 변경 단일 승자와 관심사·보드/감사 원자성을 확인한다. 루트 VERIFY_BASE=fd28a09 make verify-plan → VERIFY_JOBS=1 VERIFY_BASE=fd28a09 make verify를 실행한다.

# Impact

기존 테이블/제약을 사용하며 새 migration은 없다. slug·owner_id·에셋 참조 변경·소유권 위임·영구 삭제/정리 outbox·Shelf 정책 편집·콘텐츠/프로필·UI·운영 배포는 후속이다. 보관은 삭제가 아니며 기존 멤버·등급·Shelf·홈을 유지한다.

# Loop Alignment

요청→라우터→DI BoardService/공유 가드→모델 Repository/잠금 트랜잭션→응답이다. 서비스는 정책/흐름을, 모델은 SQL·세션·ORM 변경·DB 오류 정규화를 소유한다. 계약 타입 외 프런트 런타임·상태/UI·실시간/작업 루프는 해당하지 않는다.

# Verification

구현 전 계획을 기록했다. 시작 작업 트리는 깨끗했고 기존 UI stash는 적용하지 않는다. #36은 open/draft·main 미병합·head fd28a09임을 원격에서 확인했다. 시작 수동 검토에서 기존 BoardService는 모델 Repository와 공유 권한 가드를 DI로 사용하며 DB 세션을 직접 실행하지 않는다. 완료 시 같은 책임 경계와 도메인 예외/서비스 공개 인터페이스를 다시 검토한다.

최종 대상 API·통합·인증 68개 통과(22.62초). 권한/제공 필드, 공개·가입 정책 전환, 기존 회원/등급/홈 보존, 보관/명시 복원, 관심사 고유성/활성/순서/지우기·다른 Board 격리, no-op/stale revision·감사와 commit rollback을 확인했다. 처음 비활성 관심사 fixture가 실제 active 컬럼 대신 is_active 임시 속성을 사용해 수정했다. 이후 저장 연결과 활성 조회 필터를 구분해 격리 단언을 보완하고 PATCH 응답의 활성 필터도 기존 GET과 일치시켰다. 생략한 비활성 연결은 보존하고 감사는 저장값을 기록한다. 임시 진단 로그를 제품 소스에 추가하지 않았다.

최종 실제 PostgreSQL 검사 1개 통과(1.36초). 동일 revision 변경의 단일 승자/409·보드 설정 감사 1건, 관심사/메타데이터/감사 rollback, 보관/복원·public/members 정책 유지와 기존 멤버 읽기, no-op을 확인했다. 기존 생성·가입·등급/초대·계정 상태 경쟁·migration 왕복 및 임시 schema 정리도 통과했다. 로그는 `.git/board-settings/postgres-final.log`다. 새 테이블/컬럼은 없어 migration을 추가하지 않았다.

루트 VERIFY_BASE=fd28a09 make verify-plan 이후 VERIFY_JOBS=1 VERIFY_BASE=fd28a09 make verify 전체 15명령 통과(421.0초). 백엔드 686 통과/PG opt-in 1 skip(위 별도 통과), 프런트 단위 207·브라우저 250·production 18·style-studio 3 및 아키텍처·계약/생성 타입·설정/도구·빌드/패키징 통과. 모델/공유 권한/계약 변경으로 전체 범위를 유지했고 수동으로 축소하지 않았다. 로그는 `.git/verification-logs/run-f2lyla05`, 계획은 `.git/board-settings/verify-plan.log`다.

완료 수동 검토: 라우터는 DI BoardService.update만 호출하며 역할/최종 상태는 서비스/공유 가드에서 검사한다. 다른 서비스의 private 접근·서비스의 DB 세션/SQL·ORM 쓰기·DB 예외 해석은 추가하지 않았다. 기존 모델의 Board 잠금 안에서 설정·관심사 연결·revision·감사를 원자적으로 저장하고 현재 DB 권한을 사용한다. 보드 설정 감사는 회원 상태와 분리된 허용 DTO로 조회하며 raw changes/계정 비공개 필드를 반환하지 않는다. 오류는 영어 기본 문구·도메인 enum·공통 응답 빌더를 유지한다. 새 UI/프런트 상태·실시간/작업·배포는 없어 해당 루프의 새 화면/성능 측정은 생략했다.

양쪽 OpenAPI·생성 타입과 한국어 문서를 동기화했다. #37과 상위 #22/#1에서 구현·검증·초안 PR·main 병합을 구분한다. 선행 #36과 이번 변경의 main 병합·운영 배포는 수행하지 않는다. 푸시 훅은 우회하지 않고 동일 입력의 유효한 검증만 재사용한다.
