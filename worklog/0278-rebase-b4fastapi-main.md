# Commit Title

chore: 최신 B4FastAPI 기반으로 Canvanity 이력을 재정렬한다

# Changed File Scope

upstream/main 이후 Canvanity의 기존 초기화·브랜드·캔버스·Board 커밋, 충돌한 계층 문서/규칙과 코드. 별도 가입/탈퇴 stash는 적용하지 않는다.

# Reason

사용자 요청에 따라 B4FastAPI의 백엔드 계층 정리 커밋을 Canvanity의 기반 이력으로 반영한다.

# Design

기존 main과 upstream SHA를 Git 내부 기록과 별도 백업 브랜치에 보존한다. 작업 브랜치에서 기존 merge 구조를 유지하는 rebase-merges로 최신 upstream/main 위에 Canvanity 커밋을 재적용한다. 공용 백엔드 계층 개선과 Canvanity의 단일 저장소·한국어·브랜드·Board 기능을 함께 보존한다. upstream은 읽기 전용이며 원격 main은 별도 승인 없이 재작성하지 않는다.

# Verification Plan

충돌 표식/미병합 파일·upstream ancestor·전후 파일 차이와 stash 보존을 검사한다. 최신 기반 변경으로 루트 make verify-plan → make verify 전체 검증과 PostgreSQL Board 검사를 실행한다. API 계약과 한국어 문서·규칙을 확인한다.

# Impact

작업 브랜치의 Canvanity 커밋 SHA가 바뀐다. 원래 main/원격 이력과 보존된 가입 작업은 유지한다. DB 스키마·신규 제품 기능은 추가하지 않는다.

# Loop Alignment

기존 요청→라우터→서비스→모델/저장소와 프런트 API 상태 루프를 유지한다. 새 실시간/백그라운드/네이티브 기능은 추가하지 않는다.

# Verification

기준: 기존 Canvanity main 370a5e3bef5065fc4fe6b8a981e9fa1514d9bb81, 새 upstream/main ff11967(PR #160, 7cc0a13·eb29e44). 기존 Canvanity 커밋 12개와 merge 구조를 rebase-merges로 새 기반 위에 재생성했다.

충돌 4파일: AGENTS.md·src/backend/BACKEND.md·README.md는 Canvanity 단일 저장소/한국어 지침에 upstream의 최신 책임 경계를 통합했다. AGENTS.ko.md도 일치시켰다. main.py는 upstream BootstrapService.client_config 위임을 유지하면서 Canvanity Interest/Board 라우터를 보존했다. 가입/탈퇴 stash는 새로 만들거나 적용하지 않았다.

수동 경계 검토에서 Canvanity 전용 InterestService에 남은 IntegrityError 변환을 발견했다. 최신 upstream 규칙과 같은 모델 오류 정규화를 위해 InterestRepository.create/update로 옮겼으며 기존 오류 코드·API 계약은 유지한다. Board 저장소/권한 서비스와 upstream의 API 키 인증·결제·프로필 사진의 저장소 경계를 함께 확인한다.

최종 `VERIFY_BASE=upstream/main VERIFY_JOBS=1 make verify` 15명령 통과(148.9초, run-_f6wcs1i). 백엔드 530 통과/명시 PG 1 skip, 계약/패키징 검사 통과. 변경 없는 프런트엔드의 일치하는 24시간 내 검증 결과를 재사용했다. 별도 실제 PostgreSQL Board migration 왕복·slug/생성 한도 경쟁·복합 FK·삭제 검사 통과.

range-diff로 기존 작성 커밋 12개 중 10개는 패치 동일, 초기화/프로필 2개는 충돌 해결에 따른 차이만 있음을 확인했다. upstream/main이 새 브랜치의 조상이며 프런트 전체·계약·Board 코드의 트리는 기존 main과 동일하다. 충돌 표식/미병합 파일 없음, AGENTS.md·AGENTS.ko.md 일치. 수동 경계 검색에서 서비스/인증 의존성의 SQLAlchemy·DB 세션 접근은 admin 엔진 메타데이터 예외만 남았다. main.py /config는 BootstrapService를 사용하고 Interest 오류 변환은 모델에 둔다.

원래 main 370a5e3과 별도 백업 브랜치를 보존했다. 기존 가입/탈퇴 stash는 그대로이며 새 stash 작업은 하지 않았다. 원격 main 교체는 이력 재작성 금지 규칙 때문에 사용자 확인 전 수행하지 않는다.
