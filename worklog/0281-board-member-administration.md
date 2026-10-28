# Commit Title

feat: 보드 회원 역할과 등급 및 제재 관리 API를 구현한다

# Changed File Scope

Board 모델·권한/회원 운영 서비스·라우터/오류, API/실제 PostgreSQL 회귀, 양쪽 OpenAPI와 생성 타입, 한국어 도메인 문서. 제품 UI는 제외하며 기존 UI 회귀의 소수점 단언만 수정한다. 추적 #31, 상위 #22/#1.

# Reason

가입 이후 운영자가 회원을 조회하고 기존 등급을 수동 부여하며 운영 역할·제재를 관리할 수 있어야 한다. 활동 등급과 운영 권한을 분리하고 Owner·계정 개인정보를 보호한다.

# Design

회원 목록과 감사 조회는 cursor pagination·허용 필터·현재 Board 역할을 사용한다. Owner/Admin은 회원 운영 필드를 보고 Moderator는 제재 가능한 active 일반 회원의 최소 공개 프로필만 본다. PATCH는 expected_revision/reason과 role/status/grade_id를 받고 모든 필드의 위계/최종 상태를 확인한 뒤 모델의 같은 Board 잠금 트랜잭션에서 변경·revision·이전/이후 감사 기록을 저장한다. 본인/Owner 변경과 role=owner, 타 Board 등급을 거부한다. Admin은 Owner/Admin을 관리하지 못하고 Moderator는 일반 active 회원의 정지/차단만 수행한다. 서비스에 SQL·세션·ORM 저장 필드 변경을 넣지 않는다.

# Verification Plan

기준 265ee35에서 루트 verify-plan → verify. 역할/상태/필드 행렬, 개인정보 및 타 Board 경계, stale revision·감사 롤백·권한 즉시 반영, 목록 cursor·감사 기간 180일·동시 변경을 API와 실제 PostgreSQL에서 확인한다. 계약·생성 타입·수동 계층 경계도 검토한다.

# Impact

기존 테이블을 재사용하고 회원/감사 keyset 조회용 복합 인덱스만 0025 migration으로 추가한다. 등급 정의 CRUD·초대·소유권 위임·Board 종료·UI는 후속이다. 계정 전역 역할·이메일·인증 데이터는 변경/노출하지 않는다.

# Loop Alignment

요청→라우터→DI 서비스/공유 권한→모델 Repository→응답을 따른다. 권한은 요청마다 현재 DB에서 읽는다. UI·실시간·백그라운드 작업은 추가하지 않는다.

# Verification

구현 전 계획을 기록했다. 회원 운영·인증 통합 검사 63개 통과. 역할/필드 위계, Moderator 최소 프로필, 타 Board 등급·전역 Admin 경계, 즉시 강등/차단, stale revision/no-op, 감사·membership/revision 롤백, 기간/커서/동일 시각 정렬을 확인했다. 추가 ID 범위·시간대 경계 검사를 포함한 최종 회원 운영 대상 38개도 통과했다.

실제 PostgreSQL에서 같은 revision의 수동 변경 두 요청 중 하나만 성공하고 나머지는 409, 감사 1건·revision 1회 증가를 확인했다. 외부 등급과 제재를 섞은 요청 전체 거부, 0025 인덱스 존재, migration downgrade/re-upgrade와 임시 schema 제거도 통과했다.

수동 경계 검토: 라우터→BoardMembershipService, 공개 BoardPermissionService 가드, 모델 공개 도메인 메서드만 사용한다. 서비스/인증 의존성의 SQLAlchemy·DB 세션 접근은 admin 엔진 메타데이터 예외만 남는다. DB 쓰기와 감사는 모델, 권한·상태/기간·cursor 판단은 서비스에 있다. 신규 UI 소스는 변경하지 않는다. 최초 전체 실행은 백엔드 576 통과/명시 PG 1 skip, 프런트 단위 207 통과. 기존 SegmentedControl 회귀 한 건만 DOMRect 높이 32.000030517578125를 32 이하와 비교해 실패했다(UI 249 통과). 실제 UI 코드는 수정하지 않고 해당 단언을 0.01 CSS px 정밀도로 반올림해 기존 32px 기준을 유지했다.

PATCH의 생략 가능 필드가 OpenAPI에서 nullable로 표현되던 점도 수정했다. SkipJsonSchema와 모델 스키마 훅으로 명시적 null 금지·변경 필드 최소 하나를 JSON Schema/생성 타입에 반영하고 계약 회귀를 추가했다.

최종 검증: `VERIFY_BASE=265ee35 make verify-plan`과 `VERIFY_JOBS=1 VERIFY_BASE=265ee35 make verify`를 루트에서 실행했다. 전체 범위 15개 명령 모두 통과(481.0초). 백엔드 577 통과/명시적 실제 PG 대상 1 skip, 프런트 단위 207·UI 250·production 18·style-studio 3 통과. 실제 PG 대상은 별도 실행으로 통과했다. 아키텍처·계약/생성 타입·도구/설정·빌드/패키징 검사도 통과했다. 로그는 `.git/verification-logs/run-od3yk20p`, 실제 PG는 `.git/member-admin/final-postgres.log`에 보존한다. 최종 코드에 대한 검증을 반복하지 않고 훅의 유효한 receipt 재사용을 허용한다. #31에서 구현·검증·초안 PR·main 병합 상태를 구분하고, 다음 등급 정의 관리는 #32로 추적한다.
