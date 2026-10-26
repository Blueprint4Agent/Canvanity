# Commit Title

docs: 커뮤니티 도메인과 등급 권한 및 개발 검증 기반을 설계한다

# Changed File Scope

- notes/community/: 도메인·데이터·권한·API·개발 검증·편집 엔진 설계와 검증 fixture.
- PROJECT_BRIEF.md: 후속 설계 문서 진입점.
- worklog/0273-community-domain-architecture.md: 계획과 실제 결과.

# Reason

이슈 #3/#4/#5의 1단계를 진행한다. Board·Shelf·Canvas와 운영 역할·회원 등급·상태·정책을 분리하고 다음 구현이 사용할 계약과 재현 가능한 검증 근거를 만든다.

# Design

1. 현재 모델·API·실행 환경·공용 캔버스를 조사한다. 시크릿은 출력하거나 변경하지 않는다.
2. ERD·필드·제약·생성 트랜잭션·상태 전이·권한 행렬·API 명세·마이그레이션 순서를 작성한다.
3. 격리된 검증으로 PostgreSQL 제약/동시성 및 편집 엔진 저장·복원·입력 동작을 확인한다. 실제 관측과 설계/후속 구현을 구분한다.
4. 루트 검증과 문서/fixture 검사를 실행하고 이슈 진행 기록을 갱신한다.

# Verification Plan

- 기준 커밋: 5b1adf8b15348e228b97b61ad5f083bf6b49fb96.
- VERIFY_BASE=<기준 커밋> make verify-plan → make verify.
- 문서 상대 링크·git diff --check·계약 불변 확인.
- 격리된 PostgreSQL 제약/경쟁 갱신 실험 및 편집기 round-trip/브라우저 입력 검증. 외부 제공자를 호출하지 않는다.
- 대상 파일 스테이징 후 COMMIT_TITLE/COMMIT_BODY_FILE로 make git-governance-check.

# Impact

1단계 설계와 검증용 fixture만 추가한다. Board/Shelf/Canvas 제품 API·운영 스키마·외부 제공자·배포는 이번 단계에서 적용하지 않는다.

# Loop Alignment

요청→서비스→DB→응답 및 페이지→훅→타입 API→상태→UI 경계를 설계한다. 실시간/작업 루프는 후속 범위와 책임만 정의한다. 제품 런타임·데스크톱 루프 변경은 없다.

# Verification

- 기준 전체 verify-plan은 새 notes probe 경로를 shared/unknown으로 판정하여 backend=True/frontend=full, 15개 명령을 선택했다. 수동 강등하지 않았다.
- 첫 `VERIFY_BASE=5b1adf8b15348e228b97b61ad5f083bf6b49fb96 make verify`: 15명령/279.2초 통과. 로그 `.git/verification-logs/run-t2dxle1y/`. 백엔드 516(기존 경고 37), 단위/통합 207, UI 245, 프로덕션 18, Style Studio 3개 통과.
- PostgreSQL 16.13: 격리 schema에서 11개 검사 통과, schema 삭제 후 부재 확인. 1,000 text 노드 195,935 bytes, 전체 JSONB 갱신 10회 2.264~8.138ms(제품 API 지연 아님).
- Excalidraw 0.18.1/React 18.3.1: 독립 브라우저 검사 9개 통과. 입력/undo·redo/이미지 drop·합성 paste/5요소 canonical JSON·reload/모바일 렌더링. 증거 `.git/community-probes/editor.json`과 desktop/mobile PNG.
- 초기 skeleton 정규화와 undefined 속성의 JSON 소실 때문에 복원 비교가 실패했다. 엔진 restore 경로와 JSON canonicalization을 적용해 좌표/본문/순서 비교를 유지한 채 통과했다. debug-live 세션 시작은 응답하지 않아 breakpoint 제거/stop 후 브라우저 evaluate로 값만 조사했다.
- 독립 production build 통과. 큰 chunk/use-client 무시 경고를 기록했다. 실제 production 폰트 경로·제품 번들은 채택 조건으로 남긴다.
- 로컬 환경 감사·make db-current(0023 head), 문서 8개 상대 링크 누락 0, Ruff/Prettier, git diff --check 통과. 제품 OpenAPI/생성 타입/의존성/운영 migration diff 없음.
- OS 네이티브 IME·실기 펜/압력·실제 모바일 pinch/대표 이미지 부하·제품 API 권한/서버 저장은 미검증이다. #4를 완료로 처리하지 않는다. 기존 env·서비스·시크릿을 변경하거나 외부 제공자를 호출하지 않았다.
- 최종 수정본 verify-plan은 같은 전체 범위를 유지했다. `make verify` 15명령/100.5초 통과(7명령 실제 실행, 입력/환경/출력이 일치한 프런트엔드 8명령 receipt 재사용). 로그 `.git/verification-logs/run-wm71d79s/`. 첫 279.2초 전체 실행과 재사용 포함 시간을 구분한다.
- 대상 17파일만 스테이징하고 COMMIT_TITLE/COMMIT_BODY_FILE 지정 governance 검사 통과. 이번 요청에서 commit/push/PR/배포는 실행하지 않았다.
- 이슈 #1/#3/#4/#5/#6/#22/#23에 로컬 산출물·검증 결과·구체화한 계약/미검증 범위를 반영했다. 소유자 계정 삭제의 종료 경로(소유권 이전/보관 후 Board 영구 삭제·파일 삭제 outbox)를 #22/#6과 함께 출시하도록 기록했다. 이슈는 열린 상태다.

# State Ownership

제품 프런트엔드 변경 없음. 검증 fixture의 영속 문서와 임시 선택·카메라 상태를 구분한다.

# Memoization

제품 React 변경 없음. 무차별 memo를 도입하지 않는다.

# Performance Evidence

측정 fixture와 실제 관측 결과를 편집 엔진 검증 문서에 기록한다. 미측정 결과를 보장하지 않는다.

# Page Family

## Family

제품 UI 변경 없음. 격리된 기술 검증 화면만 대상이다.

## Reference

기존 CommunityCanvas/ExploreCanvas와 공용 카메라 규칙.

## Shared Rules

유한 좌표·팬/줌·입력 중 단축키 경계와 영속/임시 상태 분리를 검토한다.

## Exceptions

검증 화면은 서비스 라우트에 추가하지 않는다.

## Evidence

1440×1000·390×844 독립 화면을 시각 확인했다. 실제 제품 UI 변경은 없고 엔진의 유한 카메라/공용 도구 통합은 남은 채택 조건이다.

# Publication

사용자 후속 요청에 따라 기존 검증 결과를 사용해 커밋·푸시·PR 생성과 merge commit 자동 병합을 진행한다. 별도 테스트를 다시 실행하지 않으며 저장소 Git 훅은 유지한다. 실제 병합 상태와 커밋 근거는 GitHub PR에서 확인한다. 앞선 미게시 기록은 해당 단계 당시의 상태다.
