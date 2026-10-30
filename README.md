# Canvanity

글·이미지·그림·손글씨를 캔버스에 배치해 공유하는 캔버스 기반 커뮤니티 프로젝트다.
Board·회원/등급·Shelf와 Canvas 초안·이미지 저장 기반을 단계별로 개발 중이다. 구현·main 병합 상태는 [커뮤니티 문서](notes/community/README.md)와 연결 이슈/PR에서 구분한다.

[B4FastAPI](https://github.com/Blueprint4Agent/B4FastAPI)를 포크했고,
[B4React](https://github.com/Blueprint4Agent/B4React)의 고정 소스를 src/frontend에 직접 편입했다.
백엔드와 프런트엔드는 같은 Git 저장소에서 관리하며 서브모듈 초기화가 필요 없다.

## 빠른 시작

Git·Make·Python 3.11 이상·uv·Node.js 24·npm을 준비한다.

```sh
git clone https://github.com/Blueprint4Agent/Canvanity.git
cd Canvanity
make init
make install
make project-init
make project-check
```

개발은 별도 터미널에서 실행한다.

```sh
make backend-dev
make frontend-dev
```

백엔드 기본 주소는 http://localhost:8000, 프런트엔드는 http://localhost:5173이다.
모놀리식 정적 패키징은 make frontend-package로 수행한다. 운영 배포는 별도 설정과 검증이 필요하다.

## 기본 설정

- 이름: Canvanity / 슬러그: canvanity
- UI: 한국어 기본, 기존 영어 전환 유지
- 로그인 활성화, 이메일·OAuth 비활성화. 이메일 가입/비밀번호 복구 등 이메일 의존 기능은 제공자 설정 전까지 사용할 수 없다.
- 개발 문서·커밋·PR: 한국어. 자동화용 타입·섹션 이름은 유지한다.
- 아이콘·로고·파비콘은 사용자 제공 파란 C 마크를 사용한다. 라이트/다크 블루 테마와 자산 원본은 [브랜드 가이드](branding/README.md)를 따른다. 기존 UI 소개용 이미지는 Canvanity 브랜드와 모의 데이터를 사용한 예시이며 캔버스 서비스의 실제 화면이 아니다.
- [Canvas 이미지 API와 파일 정리](notes/community/canvas-assets.md)를 구현하며 본문 편집 저장·게시/공유·협업은 후속 개발 범위다.

## 개발 문서

- [프로젝트 개요와 범위](PROJECT_BRIEF.md), [초기화 감사](PROJECT_INITIALIZATION_AUDIT.md)
- [에이전트 규칙](AGENTS.md), [프로젝트 설정](PROJECT_SETUP.md), [배포](DEPLOY.md)
- [백엔드 가이드](src/backend/BACKEND.md), [백엔드 빠른 시작](src/backend/README.md)
- [프런트엔드 가이드](src/frontend/FRONTEND.md), [프런트엔드 빠른 시작](src/frontend/README.md)
- [API 계약](contracts/README.md), [검증](notes/verification.md), [통합 프런트엔드](notes/frontend-submodule.md)

기존 한국어 번역은 notes/ko에도 보존한다. 현재 활성 문서의 단일 저장소 지침을 우선한다.
원본 라이선스·출처·기술 식별자·과거 worklog를 유지한다.

## 검증

```sh
make verify-plan
make verify
make git-governance-check
```

원격 저장소는 [Blueprint4Agent/Canvanity](https://github.com/Blueprint4Agent/Canvanity)이며 B4FastAPI의 실제 GitHub fork다.
초기화 변경의 게시 상태는 프로젝트 개요에서 확인한다.
