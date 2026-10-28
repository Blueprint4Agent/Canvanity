# Commit Title

feat: 보드 회원 등급 설정 API를 구현한다

# Changed File Scope

Board 모델/저장소·DI 등급 서비스·공유 권한 가드·라우터/오류, API/실제 PostgreSQL 회귀, 양쪽 OpenAPI·생성 타입·통합 계약 출처/README, 한국어 도메인 문서. #32, 상위 #22/#1. 제품 UI는 제외한다.

# Reason

Board 운영자가 기본 뉴커머/피너/큐레이터를 포함한 등급 이름·순서·기본값을 변경하고 참조를 안전하게 대체할 수 있어야 한다. 회원에게 기존 등급을 부여하는 #31과 등급 자체의 설정을 분리한다.

# Design

선행 초안 PR #33의 `b397069`에서 작업 브랜치를 분리한다. #33은 main 미병합이므로 새 PR은 해당 브랜치를 기준으로 등급 설정 차이만 표시한다. 조회는 현재 Board 공개 범위와 멤버 상태를 검사하고, 변경은 현재 active Owner/Admin만 허용한다. Board 잠금·expected_revision·등급 수/이름/rank/기본값 불변식·감사 기록을 기존 models/board.py의 같은 트랜잭션에서 유지한다. 등급 순서는 즉시 유니크 제약과 정수 범위를 지키는 두 단계 재배치로 저장한다. 삭제는 같은 Board의 대체 등급으로 회원 및 Board/Shelf 정책을 이동한 뒤 수행한다. 기본값 변경은 기존 회원 등급을 변경하지 않는다. SQL·세션·ORM 쓰기·DB 오류 해석은 모델이, 정책과 흐름은 서비스/공유 가드가 소유한다.

# Verification Plan

API 계약/인증 인벤토리, Owner/Admin/Moderator/Member·전역 Admin·타 Board·제재/보관 상태 행렬을 검증한다. 이름 변경의 ID 유지, 중복/최대 개수/마지막 등급, 기본값과 다음 가입자, 재정렬의 정책 즉시 반영, 참조 대체·stale revision/no-op·감사/참조 롤백을 확인한다. 실제 PostgreSQL에서 즉시 유니크와 FK·동시 변경·기본값 전환·삭제 대체 및 migration 왕복을 확인한다. 루트 `VERIFY_BASE=b397069 make verify-plan` 다음 `VERIFY_JOBS=1 VERIFY_BASE=b397069 make verify`를 실행하고 결과를 기록한다.

# Impact

기존 등급·회원·Board/Shelf 정책·감사 테이블을 재사용한다. 이름/rank로 운영 권한을 부여하지 않는다. 자동 승급·활동 집계·초대·위임·Board 종료·Shelf 정책 편집·UI는 후속이다. 운영 배포와 운영 DB 변경은 포함하지 않는다.

사용자 추가 검토: 예외 enum/ServiceException/응답 빌더는 기존 방식과 같으나 Board만 default_message에 한국어를 사용하고 전역 핸들러가 그대로 반환함을 확인했다. Auth/APIKey 등과 동일하게 Board의 기본 메시지를 영어로 정리하고 코드·상태·details 계약과 프런트의 코드 기반 한국어/영어 번역은 유지한다. AGENTS의 한국어 문서/UI 지침을 API 기본 메시지 번역으로 확대 적용하지 않는다.

# Loop Alignment

요청→라우터→DI 서비스/공유 권한→모델 Repository/잠금 트랜잭션→응답을 따른다. 권한은 요청 시점 데이터를 읽는다. 계약 생성 타입 외 프런트 런타임·상태·UI·실시간/작업 루프 변경은 없다.

# Verification

구현 전 계획을 기록했다. 시작 작업 트리는 깨끗하며 기존 UI stash는 적용하지 않는다. #33은 초안/open·main 미병합 상태임을 원격에서 확인했다. 시작 수동 경계 검토에서 기존 Board 서비스는 모델 트랜잭션을 사용하며 SQL/세션을 직접 실행하지 않는다. 구현 후 권한/도메인 예외·서비스 공개 인터페이스와 저장 경계를 다시 검토한다.

최종 대상 API·통합·인증 검사 61개 통과(23.32초). 최초 두 실패는 fake 서비스가 실제 응답 DTO 대신 dict를 반환한 테스트 계약과, PATCH의 선택적 이름 필드에 길이 제약을 union 바깥에서 적용해 명시적 null이 TypeError가 된 문제였다. 실제 예외 스택으로 입력/원인을 확인하고 DTO fake 및 Annotated 문자열 분기 제약으로 수정했다. 이후 명시적 null·빈 변경·is_default:false가 422이며 JSON Schema/생성 타입도 null 금지와 최소 변경 필드를 표현함을 확인했다.

최종 입력의 실제 PostgreSQL 검사 1개 통과(0.98초). 기본/rank 즉시 유니크와 INTEGER 최대값 rank 재배치, 동일 revision 기본값 변경 두 요청의 단일 승자/409, 회원·Board/Shelf 정책 이동과 기본값 이전, commit 실패의 참조·revision·감사 롤백, migration downgrade/re-upgrade 및 임시 schema 제거를 확인했다. 로그는 `.git/grade-management/postgres.log`다. 기존 스키마만 사용하므로 새 migration은 없다.

루트 `VERIFY_BASE=b397069 make verify-plan` 이후 `VERIFY_JOBS=1 VERIFY_BASE=b397069 make verify` 전체 15명령 통과(383.7초). 백엔드 611 통과/실제 PG opt-in 1 skip(위 별도 실행 통과), 프런트 단위 207·브라우저 250·production 18·style-studio 3 통과. 아키텍처·계약/생성 타입·설정/도구·빌드/패키징도 통과했다. 전체 범위를 선택한 이유는 모델/공유 권한/계약 변경이며 수동으로 축소하지 않았다. 로그는 `.git/verification-logs/run-9mnow12d`, 계획은 `.git/grade-management/verify-plan.log`다.

완료 수동 검토: 라우터는 DI 등급 서비스의 공개 메서드만 호출하고 프레임워크 상태 상수/도메인 예외 응답을 사용한다. BoardGradeService/공유 가드는 역할·상태·업무 검증을 담당하고 다른 서비스의 private 메서드를 사용하지 않는다. SQL·join/정렬·ORM 속성 변경·잠금/flush/commit·DB 오류 정규화는 기존 models/board.py에만 있다. 원본 감사 JSON을 반환하지 않고 허용 DTO로 이전/이후 등급·참조 이동 수만 노출한다. Board 기본 메시지 언어 차이는 일관성 정리였으며 enum/ServiceException/전역 핸들러 설계 자체는 기존 허용 구조다.

양쪽 계약과 생성 타입은 의미상 동기화했다. 프런트 계약 출처에 남아 있던 과거 B4FastAPI 커밋 pin을 단일 저장소 동일 커밋의 Canvanity 계약으로 정리하고 설명 문서도 갱신했다. 제품 프런트 런타임·UI·상태 변경이 없으므로 새 화면/성능 측정은 해당하지 않는다. #32에서 구현·검증·초안 PR·main 병합을 구분해 추적하고, 푸시의 필수 훅은 우회하지 않는다.
