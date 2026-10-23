# Canvanity 통합 프런트엔드

이 경로는 기존 문서 링크 호환을 위해 유지한다. Canvanity는 프런트엔드 서브모듈을 사용하지 않는다.
B4React 커밋 085b4ec07a2bf35e074750001434f93ad48745c0의 추적 파일을 src/frontend에 편입했다.
원본 출처는 https://github.com/Blueprint4Agent/B4React 이며 고정 버전은 초기화 감사에 기록한다.

별도 .git·.gitmodules·gitlink가 없으며 git clone만으로 전체 소스를 받는다.
make frontend-init은 소스 존재 확인, make init은 루트 훅과 env 초기화만 수행한다.
프런트엔드와 백엔드 변경은 같은 작업 브랜치·루트 워크로그·커밋·PR에서 검증한다.
계약은 루트/프런트엔드 스냅샷을 명시적으로 갱신하며 make contract-check와 make frontend-api-check로 검증한다.
원본 템플릿의 자식 PR 먼저 병합/부모 gitlink 갱신 절차는 이 프로젝트에 적용하지 않는다.
