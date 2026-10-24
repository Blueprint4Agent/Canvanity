# Canvanity 기본 초기화 감사

## 대상과 복구

- 실제 로컬 초기화. 원본 B4FastAPI는 수정하지 않는다.
- 대상: /Users/choi-hyk/blueprint4agent/Canvanity
- 기준 부모 커밋: d1b82aedf97b6c855977a3963ba4e02938409fb5
- 기준 프런트엔드: 085b4ec07a2bf35e074750001434f93ad48745c0, B4React 원본.
- 시작 작업 트리: 깨끗함. 프런트엔드 작업 디렉터리는 비어 있고 env/생성 자산은 없다.
- 브랜치: chore/canvanity-initialization
- origin: https://github.com/Blueprint4Agent/Canvanity.git (GitHub fork 생성 확인, 초기화 변경은 아직 푸시하지 않음)
- upstream: https://github.com/Blueprint4Agent/B4FastAPI.git (pushurl=DISABLED)
- 입력: project.json, 고정 프런트엔드 소스, 기존 한국어 번역.
- 교체되는 추적 파일의 원본 바이트/모드는 위 기준 커밋에 보존된다. 프런트엔드 원본은 위 B4React 커밋에 보존된다.
- 생성 전 env/ignored 자산 없음 확인. 새 env와 project.local.json/public/project-brand, 의존성/빌드 출력은 로컬 생성물이며 복구 시 제거 대상이다. 기존 사용자 파일은 없다.
- 초기화 훅의 .project-backups는 ignored로 유지한다. 비밀 값은 공개 기록에 출력하지 않는다.
- 전체 복구는 새 Canvanity 복제본을 제거하면 된다. 원본 저장소·env·고정 프런트엔드는 보존한다. 빌드 출력은 원본 복구 대상이 아닌 재생성 대상이다.

## 표면별 상태

각 행의 실제 검증/명시적 보류 근거를 완료 시 기록한다.

| 표면 | 경로/소유자 | 요청 결과·적용 경로 | 상태/근거 |
| --- | --- | --- | --- |
| 공통 브랜드 | project.json → frontend/project.local.json | 제목·워드마크 Canvanity | verified: production branding 4개 조합(ko/en 브라우저, 모바일/데스크톱, light/dark) 통과 |
| 보조 UI | src/frontend/src | 기본 컴포넌트 유지 | 브랜드 샘플/아바타의 템플릿 자산은 명시적 보류 |
| 브라우저 정체성 | HTML/title/lang/favicon/OG | 이름·ko 기본 적용 | verified: production branding의 실제 title/html lang 및 저장 en 유지 검사 통과. 아이콘·공유 미리보기는 명시적 보류 |
| 브랜드 자산 | branding, frontend/public, notes/assets | 원본 임시 사용 | 명시적 보류: 사용자 후속 제공 |
| UI 언어 | frontend i18n·브라우저 저장소 | 새 사용자는 ko, 선택 en 유지 | verified: production branding의 영어 OS locale→ko 및 en 저장 후 reload 검사 통과 |
| 백엔드 정체성 | APP_NAME/EMAIL_BRAND_NAME | 공개 이름 Canvanity | verified: project-check가 backend/docker APP_NAME·EMAIL_BRAND_NAME 등 소유 설정의 manifest 일치를 확인 |
| 콘솔 | backend observability | 원본 시작/종료 배너 유지 | 명시적 보류: 상세 브랜드 후속 적용, 템플릿 B4A 배너 잔존 가능 |
| 메시지 | backend mail/inbox | 기본 이름 설정, 메일 비활성 | 실발송 해당 없음; 고정 샘플 문구 브랜드 후속 점검 보류 |
| 문서 | README/AGENTS/도메인/setup/deploy/notes | 한국어 활성 진입점 | verified: 기존 유지보수 한국어 번역 적용, 루트/도메인/설정/배포/notes 활성 링크 대상 누락 0개 |
| 문서 언어 | 기존 한국어 번역 및 상대 링크 | 한국어 본문·단일 저장소 지침 | verified: 루트 및 frontend AGENTS와 README 한국어 전환, AGENTS.ko 동일, 상대 링크 검사 통과. 원본 템플릿 이력 설명은 출처로 보존하며 루트 지침 우선 |
| 커밋/PR 언어 | AGENTS·워크로그·PR 템플릿 | 한국어 본문, 자동화 표식 유지 | verified: 실제 Git 훅의 한국어 첫 글자 커밋/PR 제목 테스트 통과. 한국어 PR 템플릿 구성. 원격 PR은 이번 범위 해당 없음 |
| 공개 소개 | configured discovery | 템플릿 기본 공개 소개 제외 | verified: configured /about 및 /about/ko 2건 통과, 원본 quick-start 부재 및 Canvanity 제목 확인 |
| 데스크톱 | src-tauri | 소스 보존 | 명시적 보류: 웹 기본 초기화만 수행 |
| 기술 정체성 | 모듈/패키지/API/storage 식별자 | 호환성 유지 | 기존 기술 식별자 유지, 브랜드 변경 대상으로 간주하지 않음 |
| 출처/이력 | LICENSE/upstream/worklog | 원형 보존 | 기존 출처·과거 기록 이름 유지 |
| 기능/실행 | project.json/env/Makefile | 로그인 on, email/OAuth off | verified: project-check 및 재실행 변경 0개. 서비스 기능·배포·제공자 연동은 명시적 보류 |

## 최종 근거와 잔여 참조

- make init/install, project-plan/project-init/project-check 통과. 같은 manifest 재실행 변경 0개.
- make verify-plan은 서브모듈 편입·공유 설정/도구 변경에 전체 범위를 선택했다. make verify의 15개 명령이 모두 통과했다. 로그: .git/verification-logs/run-91avnvjh (로컬 ignored 근거).
- 백엔드 504개(기존 경고 14개), frontend unit/integration 212개, UI 253개, production 18개, style studio 3개 및 별도 브랜드 빌드·discovery·계약·패키징 통과.
- configured 공개 소개 테스트 2건은 숨겨진 title의 표시 텍스트 대신 페이지 제목 전용 API를 사용하도록 수정했고 재검사 통과했다. 실제 서비스 제목/화면 로직은 수정하지 않았다.
- 런타임/정적 자산 280개는 원본 프런트엔드 고정 커밋과 바이트 동일. 별도 .git 메타데이터 없음. 기존 기술 식별자·이벤트·저장소 키·패키지 이름 유지.
- B4A/B4FastAPI/B4React 잔여 참조: 콘솔 배너, 임시 아이콘·템플릿 샘플 이미지/스크린샷(브랜드 보류), 원본 URL·라이선스·호환성 식별자·과거 worklog/템플릿 절차(출처/이력 유지). 브랜드 완성으로 주장하지 않는다.
- 새 로고·favicon·공유 이미지·네이티브 아이콘과 메일/콘솔 상세 브랜딩은 사용자 후속 제공 시 점검한다. 이메일 실제 발송·제공자 호출·네이티브 패키징·실서비스 배포는 수행하지 않았다.
- 원본 B4FastAPI는 깨끗한 작업 트리와 기존 frontend pin을 유지한다. GitHub fork는 isFork=true, parent=Blueprint4Agent/B4FastAPI, 기존 부모 이력 410개를 보존한다. 초기화 변경의 원격 푸시/PR은 수행하지 않는다.

## 2026-10-24 브랜드 후속 적용

- 사용자 제공 파란 C 원본과 색상 참고를 branding/references에 보존하고 실사용 투명 PNG를 branding/canvanity-mark.png에 저장했다.
- project.json의 logo로 공통 웹 브랜드/파비콘/구성된 공유 메타데이터에 같은 아이콘을 적용했다. 기존 light/dark fallback 경로를 재사용한다.
- 기존 공개/인증/쇼케이스의 390/1440px × light/dark 정상 페이지 12개에서 제목·실제 PNG 응답·이미지 로드·가로넘침 없음과 OS자동 다크 일치를 확인했다. 로컬 증거: .git/brand-review/.
- 초기 수동 스모크에서 외부 API base 요청을 막아 서버오류 화면을 확인했던 결과는 정상 페이지 증거에서 제외했다. 모의 응답 순서를 수정하고 실제 페이지별 셀렉터를 기다리는 검사로 대체했다.
- 활성 소개 스크린샷8개(en/ko)는 기존 UI와 모의 데이터로 재촬영해 래스터 내부의 원본 B4A 로고도 대치했다. 새 캔버스 페이지를 만들거나 실서비스 데이터로 주장하지 않는다.
- PNG/ICO/ICNS 네이티브 아이콘 소스를 생성했고 macOS 별도 참조 파일도 대치했다. 실제 패키지 빌드·서명·설치는 검증하지 않았다.
- 명시적 light/dark와 OS자동 dark 토큰을 동기화했다. 오류·경고·성공 의미색은 유지한다. 최종 회귀 결과와 커밋/PR 근거는 worklog/0265-canvanity-brand-theme.md에 기록한다.
- 역사적 worklog·미사용 원본 템플릿 fallback·라이선스/출처는 보존한다. 현재 브랜드 설정의 실사용 화면에는 새 아이콘을 적용한다.
