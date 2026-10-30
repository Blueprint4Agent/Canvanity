# Commit Title

feat: 보드 내 Shelf 관리와 등급별 접근 정책 API를 구현한다

# Changed File Scope

기존 Board 모델/저장소와 공유 권한 평가기, DI Shelf 서비스·라우터·도메인 오류, Board 기본/Shelf 재정의 정책 API, Board 홈 연동, API/통합/실제 PostgreSQL 회귀, 양쪽 OpenAPI·생성 타입과 한국어 문서. #23, 상위 #22/#1. 제품 UI·운영 배포는 제외한다.

# Reason

운영자가 커뮤니티 분류와 등급별 읽기·게시글 작성·댓글·좋아요 정책을 관리할 수 있어야 한다. 운영 역할·활동 등급·제재 상태를 분리하고 숨김 설정을 접근 권한으로 오인하지 않도록 한다.

# Design

기준 9cae95fbf37a9e3be3d5db4a138aef16da5d200d, feat/shelf-management. 선행 초안 PR #40이 main 미병합이므로 feat/board-ownership-lifecycle을 기준으로 분리한다. SQL·세션·잠금·ORM 쓰기·드라이버 오류 변환은 기존 models/board.py에 두고 새 Repository 파일을 만들지 않는다. 서비스는 BoardRepository와 BoardPermissionService를 생성자 DI로 사용한다. 모든 변경은 현재 Owner/Admin과 active Board·expected_revision을 같은 Board 잠금 아래 검사한다. Shelf 목록·상세/직접 URL·홈은 같은 현재 등급/정책을 적용하고 관리 조회를 별도로 구분한다. Board 정책은 전체 4액션, Shelf 재정의는 null 상속을 지원한다. 정렬은 동일 Board 전체 ID를 요구하고 기본/마지막 Shelf 삭제를 보호한다. 감사·revision과 저장은 원자적으로 처리한다.

# Verification Plan

라우터 성공/인증/입력 계약, 운영 역할과 앱 전역 역할 분리·등급/제재·비공개/보관/정지 경계, 숨김/직접 조회/홈 일치, 정책 상속/재정의·등급 순서 변경/강등 즉시 반영·타 Board 등급 거부, 생성 slug·정렬 중복/누락/타 Board ID·기본/마지막 보호·no-op/stale·감사와 commit rollback을 검증한다. 실제 PostgreSQL에서 고유/FK 제약·동시 변경 단일 승자·정렬/정책 원자성과 migration 왕복을 확인한다. 루트 VERIFY_BASE=9cae95f make verify-plan → VERIFY_JOBS=1 VERIFY_BASE=9cae95f make verify를 실행한다.

# Impact

현재 Canvas 모델이 없으므로 게시글 목록/cursor·Canvas 소속 복합 FK·비어 있지 않은 Shelf 삭제 검증은 #8 연결 시 필수 후속으로 남기고 빈 목록 API를 가장하지 않는다. Smart Shelf·자동 분류·새 UI/외부 알림/작업·파일 정리는 구현하지 않는다. 현재 스키마 재사용을 우선하고 실제 ORM 제약 변경 시 migration을 함께 작성한다. #23 전체와 선행 PR의 main 병합 여부를 별도로 추적한다.

# Loop Alignment

요청→라우터→DI Shelf/정책 서비스→공유 가드→기존 모델 Repository→응답이다. 권한은 현재 DB 상태를 사용하고 공식 Board UI Canvas의 내용과 Content Canvas 책임은 유지한다. 프런트 런타임·실시간/worker·데스크톱 루프는 이번 범위에 해당하지 않는다.

# Verification

구현 전 계획. 시작 트리는 깨끗하다. 원격 PR #40 open/draft·head 9cae95f·main 미병합을 확인했다. 기존 모델/서비스 책임 경계를 읽었고 추가 SQL/세션·ORM 쓰기는 모델에서만 수행한다. 기존 사용자 stash는 적용하지 않는다. 실제 결과와 생략 이유는 완료 후 기록한다.

- 대상 API/통합/인증 93개 통과. 실제 PostgreSQL 1 passed, 2 warnings, 2.11초. 생성 경쟁과 정렬/정책 경쟁의 단일 승자·다른 요청 409, 동일 Board slug 유니크·타 Board 등급/소속 복합 FK 거부, 정렬/기본·재정의 정책/삭제 commit 실패의 데이터·revision·감사 전체 rollback 및 migration 왕복을 확인했다.
- VERIFY_BASE=9cae95f make verify-plan → VERIFY_JOBS=1 VERIFY_BASE=9cae95f make verify: 공유 모델/권한·계약 변경으로 전체 15명령 선택/통과, 615.4초. 백엔드 788 passed / 실제 PG opt-in 1 skipped / 37 warnings(위에서 실제 PostgreSQL 별도 통과), 프런트 단위 207·브라우저 250·production 18·style-studio 3 통과. 아키텍처·Ruff·프런트 타입/포맷·양쪽 OpenAPI/생성 타입·설정/도구·빌드/패키징도 통과했다. 로그: .git/verification-logs/run-3p1w4clq.
- 실제 API Key의 새 관리 경로 401과 비공개 읽기 404, 비공개/제한/없는 Shelf의 동일 응답, 등급 승급/강등·순서 변경의 같은 토큰 즉시 반영, 운영 역할 분리·일반/관리 조회·공지 정책·기본/마지막 보호·100개 한도·no-op/stale·감사를 검증했다. 404 오류 모델의 객체 존재 정보 차이를 수동 리뷰에서 통일하고 관련 검사를 전체 회귀에 포함했다.
- 기존 OpenAPI와 의미 비교: 기존 경로/연산 정의는 같고 BoardMemberAuditResponse에 nullable shelf_change/policy_change 두 필드를 추가했다. 새 5개 경로의 10연산과 19개 스키마를 추가했다. 양쪽 계약과 타입을 같은 변경에서 갱신했고 source.json의 same-commit 출처를 유지했다.
- 완료 수동 리뷰: main의 신규 등록과 라우터는 서비스 호출/전송만 담당한다. 서비스는 저장소 공개 연산·공유 가드와 DTO를 사용하며 SQL/세션/ORM 쓰기·드라이버 오류 해석이나 다른 서비스 private 호출이 없다. DB 작업과 감사/revision은 기존 모델에 두고 도메인 Exception/ErrorCode·HTTP 상수·영어 기본 메시지를 사용한다. 새 자동 경계 검사나 별도 Repository 파일을 만들지 않았다.
- 제품 UI/운영 배포·Canvas/댓글/에셋 실제 연결은 범위 밖이다. 현재 게시글 참조가 없는 Shelf 삭제만 검증했으며 #8 연결 전 비어 있지 않음 검사·복합 FK/RESTRICT·원자적 이동·공개본/cursor 정책 적용을 필수 후속으로 남겼다. #23 전체 완료와 main 병합으로 표현하지 않는다. 프런트 런타임·상태·메모화·Page Family 변경은 없다.
