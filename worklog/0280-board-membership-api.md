# Commit Title

feat: 보드 가입과 탈퇴 API를 권한 서비스와 연결한다

# Changed File Scope

Board 모델/저장소·멤버십 서비스·라우터·오류/권한, API/DB 통합 검사와 한국어 계약 문서. 추적 이슈 #29, 상위 #22/#1. 양쪽 OpenAPI와 생성 타입을 동기화한다. UI 변경은 포함하지 않는다.

# Reason

사용자 요청으로 보존한 기존 가입/탈퇴 작업을 최신 B4FastAPI 기반에서 재개한다. UI는 보류하고 실제 참여·권한·데이터 일관성부터 완성한다.

# Design

현재 main 위에 기능 차이만 3-way 병합한다. BoardRepository와 BoardPermissionService를 멤버십 서비스에 주입하며 SQL/세션/감사 저장/commit은 기존 models/board.py 안에 둔다. 공개/open 가입은 현재 기본 grade와 member/active를 부여한다. 동일 Board 행 잠금으로 가입/탈퇴/삭제를 직렬화하고 감사·revision을 같은 트랜잭션에서 저장한다. 기존 active 가입은 멱등, Owner 탈퇴와 제재 상태의 탈퇴/재가입 우회는 거부한다. 신규 운영진/등급 편집·초대/위임은 후속 범위다.

# Verification Plan

main 0a10567 기준 루트 make verify-plan → make verify. 기본 등급·역할·Owner 보호·차단/정지·초대 전용/보관·멱등성·감사 롤백·DI override·API 키 거부를 검사한다. PostgreSQL 동시 중복 가입과 마이그레이션/삭제를 검증한다. UI는 변경하지 않으며 계약/생성 타입만 맞춘다.

# Impact

기존 0024 스키마를 재사용하고 추가 migration은 없다. 신규 Bearer 가입/탈퇴 API만 추가하며 앱 전역 관리자와 Board 역할을 혼용하지 않는다. 보관한 UI 작업은 적용하지 않는다.

# Loop Alignment

요청→라우터→주입 서비스→모델 Repository→응답을 따른다. 이번 작업은 API 전용으로 프런트 상태/UI·실시간·작업 루프를 변경하지 않는다.

# Verification

구현 전에 계획했다. GitHub 백업 브랜치는 PR 안내 정리를 위해 삭제했고 리베이스 전 main 370a5e3은 원격 canvanity-before-b4fastapi-rebase-20261027 태그로 보존했다. 기존 stash는 유지하고 그 안의 백엔드/계약 차이만 재개한다. 최신 기반에서 관련 Board/API 인증 검사 46개 통과/별도 PostgreSQL 1개 skip을 확인했다. 추가 보강한 멤버십 8개 검사도 통과했다: 앱 전역 Admin·타 Board Owner가 이 Board 운영진이 되지 않음, Owner 탈퇴 차단, pending/suspended/banned의 탈퇴/재가입 우회 거부, 현재 기본 등급 부여·반복 가입/탈퇴, 가입·탈퇴 감사/멤버십/revision 롤백, DI 대체 경계.

실제 PostgreSQL 단일 격리 schema의 동시 가입에서 회원 1행·가입 감사 1건·revision 1회 증가를 확인했고 탈퇴·빈 Board 삭제·migration 왕복도 통과했다. API만 복원했고 src/frontend의 변경은 contracts/openapi.json·생성 openapi.ts뿐이다. 서비스/인증 의존성의 직접 DB 호출은 admin 메타데이터 허용 경계 외에는 없다. 최신 B4FastAPI Interest 모델 오류 정규화 등 공유 계층을 덮지 않았다.

GitHub #1/#22/#23의 완료된 기반 체크를 갱신하고 현재 API 작업을 #29로 분리했다. 최종 `VERIFY_BASE=0a10567 VERIFY_JOBS=1 make verify` 전체 15명령 통과(349.3초, run-v9kkset7). 백엔드 538 통과/명시 PG 1 skip, 프런트 단위 207, 브라우저 250, 프로덕션 18, 스타일 편집기 3 통과. 별도 실제 PostgreSQL도 통과했고 계약/생성 타입·패키징·경계 검사 통과. 범위 강등 없이 현재 작업 트리를 검증했다. 사용자 요청대로 UI 컴포넌트·페이지·상태 훅은 변경하지 않았으며 API 변경만 초안 PR에 게시해 #29와 연결한다. 신규 기능의 main 병합은 별도 상태로 유지한다.
