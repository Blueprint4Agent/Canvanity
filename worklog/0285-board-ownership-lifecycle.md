# Commit Title

feat: 보드 소유권 위임과 보관 보드 영구 삭제를 구현한다

# Changed File Scope

Board 모델/저장소·DI BoardService·공유 가드·회원 감사·라우터/오류, API/인증/실제 PostgreSQL 회귀, 양쪽 OpenAPI·생성 타입, 한국어 도메인 문서. #39, 상위 #22/#1. UI/운영 배포는 제외한다.

# Reason

Owner가 다른 활성 회원에게 소유권을 넘기거나 보관한 커뮤니티의 현재 데이터를 정리할 수 있어야 한다. 운영 역할과 활동 등급은 분리하고 Owner 회원 역할·owner_id·계정 삭제 소유 검사의 일관성을 유지한다.

# Design

기준 2f1c21565386b34b0f8c1fe887321551c8eba628, 브랜치 feat/board-ownership-lifecycle. 선행 #38은 초안/main 미병합이므로 feat/board-settings를 기준으로 별도 PR을 만든다. 위임은 현재 Owner·Board active/archived·대상 active 회원/계정을 검사한다. Board 잠금 아래 기존 Owner 역할을 먼저 Admin으로 flush해 즉시 유니크를 지키고 대상 Owner·owner_id·revision·감사를 원자적으로 변경한다. 대상 User 공유 잠금은 계정 삭제/비활성화와 직렬화한다. 현재 DELETE는 archived Owner의 전체 데이터 삭제로 확장하고 active 빈 Board 되돌리기 계약은 유지한다. DB 쿼리/트랜잭션/ORM 쓰기/오류 변환은 기존 models/board.py에 둔다.

# Verification Plan

API 입력/인증·Owner/역할·계정/멤버 상태·active/archived/suspended·self/타 Board·stale revision·등급/가입 시각 보존·새 Owner 권한/구 Owner 제한·감사/rollback을 확인한다. archived 전체 삭제·active 비어 있지 않음 거부·확인 문자열·다른 Board/계정/프로필 파일 보존을 검증한다. 실제 PostgreSQL의 부분 유니크·동시 위임 단일 승자·계정 소유 검사·삭제 rollback·migration 왕복을 확인한다. 루트 VERIFY_BASE=2f1c215 make verify-plan → VERIFY_JOBS=1 VERIFY_BASE=2f1c215 make verify를 실행한다.

# Impact

현재 Board는 avatar/cover/Canvas/asset 파일 참조가 없으므로 삭제할 소유 파일이 없다. User 프로필 파일은 보존한다. 사용하지 않는 에셋/outbox/worker를 먼저 만들지 않으며 #6 에셋 연결 전 삭제 outbox·공유 참조/재시도 통합을 요구한다. 현재 테이블을 재사용하고 새 migration은 없다. #22 전체는 파일/에셋·후속 정책 등이 남아 계속 열린다.

# Loop Alignment

요청→라우터→DI BoardService/공유 가드→모델 Repository/잠금 트랜잭션→응답이다. 권한은 현재 DB 상태에서 검사한다. 위임 감사는 허용 DTO를 사용하고 실제 파일 I/O/외부 알림·프런트 런타임·실시간/작업은 이번에 추가하지 않는다.

# Verification

구현 전 계획을 기록했다. 시작 트리는 깨끗하고 UI stash는 적용하지 않는다. #38 open/draft·head 2f1c215를 원격에서 확인했다. Board 모델에는 파일 참조가 없고 기존 프로필 파일 정리는 User/ProfilePhotoService의 책임임을 확인했다. 시작/완료 수동 책임 경계 검토를 수행한다.

- 대상 API·통합·인증: 63 passed, 4 warnings, 27.09초. 최초 테스트의 async generator에 all()을 적용한 오류를 awaited list 검사로 수정한 뒤 전체 대상을 통과했다. 제품 코드에 임시 로그를 추가하지 않았다.
- 실제 PostgreSQL: 1 passed, 2 warnings, 1.56초. Board와 User 저장소 모두 격리 schema의 get_db로 연결했다. 부분 Owner 유니크·동시 위임 단일 승자·역할/owner_id·계정 삭제 보호·위임/삭제 commit 실패 롤백·active 빈 Board 삭제 호환·migration downgrade/upgrade를 확인했다.
- 루트 VERIFY_BASE=2f1c215 make verify-plan → VERIFY_JOBS=1 VERIFY_BASE=2f1c215 make verify: 15명령 전체 통과, 416.3초. 백엔드 722 passed / PostgreSQL opt-in 1 skipped / 37 warnings(별도 실제 PostgreSQL 검사는 위에서 통과), 프런트 단위 207·브라우저 250·production 18·style-studio 3 통과. 아키텍처·린트/타입·양쪽 OpenAPI·생성 타입·설정/도구·빌드/패키징도 통과했다. 로그: .git/verification-logs/run-ccz42drq.
- 등급·상태·가입 시각 보존, 구 Owner의 즉시 권한 해제와 새 Owner 계정 삭제 보호, 허용 DTO 감사와 롤백, 현재 전체 하위 테이블 삭제, 다른 Board/계정·실제 업로드한 프로필 사진의 200/동일 바이트를 확인했다.
- 완료 수동 검토: 라우터→DI 서비스/공유 가드→모델 Repository 경계, SQL/세션/트랜잭션/ORM 쓰기·드라이버 오류 변환의 모델 소유, 도메인 ErrorCode/HTTP 상수·영어 기본 메시지, 서비스 간 private 메서드 우회가 없음을 확인했다. 기존 DELETE operation ID를 유지했고 초대의 공유 계정 잠금 이름만 일반화했다.
- 제품 UI/배포는 요청 범위에서 제외했다. 현재 없는 Board 파일 참조·Canvas·outbox/worker는 추가하지 않았으며 #6에 실제 에셋 연결 전 삭제 트랜잭션/outbox·공유 참조·저장 위치·재시도/운영 재처리 통합을 남겼다. #39의 현재 도메인 구현과 #22 전체/파일 수명주기 완료를 구분한다.
