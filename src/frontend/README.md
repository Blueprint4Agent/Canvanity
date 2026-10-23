# Canvanity 프런트엔드

B4React의 고정 소스를 편입한 React·TypeScript·Vite 기반 프런트엔드다.
독립 저장소/서브모듈이 아니며 백엔드와 같은 브랜치·커밋·PR에서 관리한다.
한국어 UI가 기본이며 기존 영어 선택을 유지한다. 캔버스 서비스 화면과 브랜드는 후속 구현한다.

## 실행과 검증

저장소 루트에서 make init, make install, make project-init을 실행한 뒤 make frontend-dev를 사용한다.
브랜드 설정은 루트 project.json이 기준이며 project.local.json은 ignored 생성물이다.
독립적인 프런트엔드 수정 확인은 이 디렉터리에서 make check, make test, make build로 수행한다.
최종 검증은 루트 make verify-plan 및 make verify를 따른다.

[개발 규칙](AGENTS.md) · [엔지니어링 가이드](FRONTEND.md) · [테스트](TEST.md) · [페이지 일관성](notes/page-families.md) · [상태와 성능](notes/react-performance.md)
