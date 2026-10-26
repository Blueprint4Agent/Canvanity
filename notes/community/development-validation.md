# 개발 환경과 검증 절차

[설계 진입점](README.md) · [공개 시나리오 fixture](probes/scenario.json)

## 현재 환경 감사 — 2026-10-26

환경 파일 값을 통째로 출력하지 않고 [allowlist 감사 스크립트](probes/audit-environment.py)와 `make db-current`로 확인했다. 연결 URL·계정·시크릿·파일 원문은 기록하지 않는다.

| 항목              | 관측 결과                                      | 판단                                                                 |
| ----------------- | ---------------------------------------------- | -------------------------------------------------------------------- |
| 공개 project.json | login=true, email=false, oauth=false           | 새 개발/배포 기준은 공개 manifest                                    |
| 로컬 기능         | login/email/oauth/stripe=true                  | 개발자 기존 설정. 이 단계에서 덮어쓰거나 외부 제공자 초기화하지 않음 |
| DB                | 로컬 PostgreSQL+asyncpg, 5432, 16.13           | 기존 DB에는 제품 migration을 적용하지 않고 고유 schema probe만 실행  |
| migration         | 0023_broaden_interest_catalog (head)           | 기존 Interest/프로필 재사용                                          |
| Redis             | 실제 Redis, 6379, 논리 DB 1                    | 현재 개발 예외. 서비스별 인스턴스 정책은 유지                        |
| Celery            | Canvanity 전용 queue/prefix 확인               | 작업/Beat를 이번 실험에서 기동하지 않음                              |
| 파일              | local object storage                           | 프로필 사진 경로를 Canvas 저장소로 전용하지 않음                     |
| 백엔드 기본 포트  | 8000                                           | 실제 기동 여부와 구분. 기동 전 포트 충돌 확인                        |
| 제품 프런트엔드   | React 18.3.1, Vite 6.4.3, 기본 5173            | 기존 잠금 의존성 보존                                                |
| 격리 편집기       | 127.0.0.1:5193, React 18.3.1/Excalidraw 0.18.1 | 제품 라우트/백엔드와 독립                                            |
| 실험 장비         | macOS arm64, Node v20.20.2, headless Chromium  | 고정 성능 보장이 아닌 로컬 관측                                      |

manifest와 로컬 기능 차이는 공개 기준을 바꾸는 근거가 아니다. 개발자의 기존 제공자 설정은 남겨 두고 검증은 **서버 startup 없이** DB probe와 독립 편집기로 수행한다. 이후 제품 E2E 서버는 별도 환경에서 EMAIL_ENABLED=false/OAUTH_ENABLED=false/STRIPE_ENABLED=false, 테스트 DB·별도 파일 루트를 지정해 시작한다. 기존 env를 복사/덮어쓰거나 make project-init으로 자동 교체하지 않는다.

## 재현 명령

저장소 루트에서 시작한다. 백엔드 잠금 의존성은 `make backend-install`, 제품 프런트엔드는 `make frontend-install`로 준비한다. 검증 전용 편집기 의존성은 제품 package.json/lockfile과 분리된다.

```bash
cd src/backend
uv run python ../../notes/community/probes/audit-environment.py
uv run python ../../notes/community/probes/postgres.py
```

probe DDL은 소속/유니크/CAS 의미론을 확인하는 최소 모델로 정수 ID를 사용한다. 제품 UUID 타입·완성된 Alembic 마이그레이션 전체를 검증한 것은 아니다.

PostgreSQL probe는 현재 backend 설정을 사용하되 localhost/127.0.0.1/::1의 postgresql+asyncpg만 허용한다. UUID가 붙은 고유 schema를 만들고 복수 연결의 동시 CAS를 검사한 뒤 finally에서 DROP SCHEMA하고 존재하지 않음을 재확인한다. 기존 테이블을 조회·수정하지 않는다. 제품 인증·Redis·메일·Stripe·worker는 호출하지 않는다. 중단/프로세스 강제 종료 때 finally는 보장되지 않으므로 `canvanity_probe_` 접두사의 본인 실험 schema만 조사·정리한다. 공용 schema나 다른 실행의 schema를 일괄 삭제하지 않는다.

편집기 별도 터미널:

```bash
npm ci --prefix notes/community/probes/editor
npm run dev --prefix notes/community/probes/editor
```

다른 터미널:

```bash
npm run check --prefix notes/community/probes/editor
npm run build --prefix notes/community/probes/editor
```

Playwright Chromium이 없으면 해당 디렉터리에서 `npx playwright install chromium`으로 준비한다. strictPort 때문에 5193 점유 시 임의의 기존 서버를 종료하지 않고 충돌을 해결한 뒤 실행한다. 종료는 검증용 터미널 Ctrl+C. 생성물 node_modules/dist와 `.git/community-probes/` 증거는 Git에 포함하지 않는다. 본인 검증 디렉터리의 생성물만 정리한다.

## PostgreSQL 관측

[재현 스크립트](probes/postgres.py)의 11개 검사가 통과했다.

- Board slug·Board 내부 Shelf slug 고유성.
- 타 Board Shelf/Grade 복합 FK 거부.
- 기본 등급·Owner 중복 거부, deferred rank 유니크를 이용한 순서 변경.
- Board 생성 도중 FK 실패 후 Board/등급/Shelf 전체 rollback.
- 두 연결이 같은 revision을 저장하면 정확히 하나만 성공.
- 공개 snapshot 생성 후 초안 저장이 공개본을 변경하지 않음.
- 한글 1,000 text 노드/195,935 UTF-8 bytes의 JSONB 저장·로드 의미 동등성.

10회 로컬 JSONB 전체 갱신 시간은 2.264~8.138ms였다. 네트워크/API 권한·JSON 검증·직렬화·동시 사용자 부하를 포함하지 않는 DB 실험이며 제품 저장 지연시간으로 해석하지 않는다. 실험 종료 후 schema 부재를 확인했다.

## 테스트 책임 분리

| 검증                                   | 현재 결과/후속 책임                                                |
| -------------------------------------- | ------------------------------------------------------------------ |
| 설계 DDL/JSONB/CAS                     | probe 실측. 제품 migration과 repository 구현 시 통합 테스트로 이관 |
| 권한 행렬                              | 명세 확정. 제품 BoardPermissionService/API는 #22/#23에서 구현·검증 |
| 에디터 입력·브라우저 메모리 round-trip | 독립 엔진 실측. [검토 결과](editor-decision.md) 참조               |
| Canvas API/서버 저장/에셋 수명         | 아직 미구현. #6/#7/#8의 실제 수직 흐름에서 검증                    |
| 외부 스토리지·메일/OAuth/결제·배포     | 이번 단계 미실행                                                   |

기존 pytest integration_client는 임시 SQLite DB와 local object storage, mock/Null 외부 제공자를 사용한다. 새 PostgreSQL 통합 fixture는 고유 schema·연결별 search_path·정리를 재사용하도록 구현한다. 실제 계정용 시드는 기존 SeedUserSchema/SeedProfileSchema 규칙을 따르고 공개 scenario.json의 역할/등급 조건을 매핑한다. fixture의 논리 key는 제품 ID나 자격증명이 아니다.

API mock은 오류·로딩 UI를 검증하는 용도다. 실제 DB 저장으로 표기하지 않는다. 제품 E2E는 승급 전 거부→승급 후 작성→저장/재열기→게시→타인 열람→강등/차단 후 거부까지 검증한다. 서버/worker/Beat를 동시에 무조건 기동하지 않으며, 비동기 정리 검증이 필요할 때만 worker를 시작한다. Beat 상태 파일은 Canvanity 전용 로컬 경로를 지정하고 원본 B4FastAPI 상태 파일을 공유하지 않는다.
