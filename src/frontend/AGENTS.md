# Canvanity 프런트엔드 에이전트 가이드

저장소 루트 AGENTS.md가 최상위 규칙이다. 이어서 FRONTEND.md와 테스트 변경 시 TEST.md를 읽는다.

이 디렉터리는 B4React에서 편입한 Canvanity 소스이며 독립 Git 저장소나 서브모듈이 아니다.
작업 브랜치·커밋·워크로그·PR·훅은 저장소 루트에서 단일 관리한다. 별도 B4React PR이나 gitlink 갱신을 하지 않는다.
문서·커밋·PR 설명은 한국어로 작성한다. 기술 타입/자동화 섹션과 기존 API 식별자는 유지한다.

- 계약은 로컬 contracts/openapi.json으로 타입을 생성한다. 백엔드 계약 변경과 함께 루트에서 명시적으로 동기화한다.
- 일반 프런트엔드 도구는 현재 디렉터리 입력을 사용한다. 공개 브랜드 입력은 루트 project.json에서 make project-brand로 생성한다.
- 상태·React 성능: notes/react-performance.md를 따른다. 상태 소유권, memo 적용/미적용 이유, 실제 검증 근거를 루트 워크로그에 남긴다.
- UI: notes/page-families.md 및 공용 컴포넌트/스타일을 재사용한다. 새 공용 UI는 쇼케이스와 실제 비교 근거를 추가한다.
- API 상태·실시간 복구·UI 구성 루프를 따르고, 데스크톱 복구는 해당 타깃에서만 적용한다.
- make check, make test, make build 등 로컬 도구를 유지한다. 최종 범위와 통합 검증은 루트 make verify-plan, make verify가 소유한다.
- 캔버스 화면/브랜드/네이티브 패키지는 현재 기본 초기화에서 보류했다. PROJECT_BRIEF.md의 범위를 따른다.
