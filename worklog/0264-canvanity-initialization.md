# Commit Title

chore: 캔버스 커뮤니티 Canvanity 기본 초기화

# Changed File Scope

프로젝트 설정·한국어 개발 문서·프런트엔드 소스 편입·초기화/검증/빌드 도구.

# Reason

B4FastAPI에서 파생한 Canvanity를 독립 저장소로 준비한다. 캔버스 커뮤니티의 상세 화면과 브랜드는 추후 구현한다.

# Design

기존 부모 이력을 보존하고 고정된 B4React 소스를 일반 디렉터리로 편입한다. 공개 project.json으로 한국어 기본 언어와 이름을 적용한다. 기존 한국어 문서를 활성 진입점으로 사용하고 같은 저장소의 단일 커밋·PR 절차로 통합한다. 사용자 데이터·API 계약·DB 스키마는 변경하지 않는다.

# Verification Plan

make init/install, project-plan/project-init/project-check, 재실행 멱등성, make verify-plan 및 make verify, 한국어 기본/영어 선택 유지 브라우저 검사, Git 인덱스 모드·중첩 저장소·문서 링크·원본 보존 확인.

# Impact

새 로컬 프로젝트만 변경한다. 이메일·OAuth는 기본 비활성화한다. 사용자의 fork 확인 요청에 따라 Blueprint4Agent/Canvanity 실제 GitHub fork는 생성했다. 초기화 변경의 푸시·PR·배포는 이번 로컬 기본 초기화 범위에서 수행하지 않는다.

# Loop Alignment

기존 요청·API 상태·실시간 루프는 그대로 유지한다. 도메인 화면·API·이벤트·백그라운드 작업을 추가하지 않아 새 루프는 해당 없다. 네이티브 타깃과 브랜드 작업은 보류한다.

# Verification

make init/install 및 project-plan/project-init/project-check 통과. 재실행 변경 0개.
make verify-plan → make verify 전체 범위(15개 명령) 통과, 144.3초. 이번 최종 실행은 기존 내용과 다른 입력으로 receipt 재사용 없이 실행했다.
백엔드 504개, 프런트엔드 unit/integration 212개, UI 253개, production 18개, style studio 3개 통과. 별도 임시 브랜드 빌드, API 계약/타입, discovery, 모놀리식 패키징 통과.
루트 하네스 55개, 훅 9개, 성능/페이지 검토 14개 테스트 통과. 프런트엔드 하네스도 통과.
configured /about 검사 2건은 기존 hidden title 표시 텍스트 assertion 문제를 페이지 제목 전용 검증으로 고쳤으며 focused 2개 및 전체 UI 재검사 통과.
런타임/정적 자산 280개 바이트 동일, 중첩 .git 없음, 활성 문서 상대 링크 누락 0개, 원본 B4FastAPI 작업 트리와 고정 frontend pin 보존 확인.
브랜드/화면/도메인 기능/운영·제공자·네이티브는 사용자 지정 범위에 따라 보류했으며 해당 실제 연동/실발송 검사는 하지 않았다. 백엔드의 기존 경고 14개와 잠금 의존성 설치에서 보고된 기존 npm 취약점 3개(2 moderate, 1 high)는 의존성 변경 없이 유지했고 별도 보안 수정으로 처리하지 않았다.
최종 결과 문서 갱신 후 make verify-light와 스테이징 메타데이터 거버넌스를 추가 실행한다. 코드·설정은 전체 검사 후 변경하지 않는다.

# State Ownership

고정된 B4React 소스를 그대로 편입한다. 기존 AuthProvider/도메인 훅이 상태를 소유하며 새 저장소나 API 상태를 추가하지 않는다.

# Memoization

기존 AdminUserTable 등 memo 경계를 원형대로 보존한다. 새 컴포넌트와 상태 변경이 없어 추가 memo는 필요 없다.

# Performance Evidence

기존 프런트엔드 검사·단위 테스트와 전체 브라우저 검사를 실행한다. 실제 최종 결과는 Verification에 기록한다. 성능 개선 수치는 주장하지 않는다.

# Page Family

## Family

기존 공개/인증/앱 셸을 그대로 편입한다. 서비스 전용 캔버스 화면은 후속 단계다.

## Reference

B4React 085b4ec07a2bf35e074750001434f93ad48745c0의 기존 화면이 기준이다.

## Shared Rules

기존 셸·공용 UI·CSS를 변경 없이 사용한다. project.json의 이름·언어 오버라이드만 적용한다.

## Exceptions

로고·파비콘·샘플 이미지는 사용자 결정에 따라 템플릿 임시 자산을 유지한다.

## Evidence

런타임 TSX/CSS 파일은 원본 고정 커밋과 바이트 비교한다. 전체 UI 및 프로덕션 브랜드 검사 결과는 Verification에 기록한다.
