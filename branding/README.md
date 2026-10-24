# Canvanity 브랜드 자산과 테마

- 실사용 아이콘: [canvanity-mark.png](canvanity-mark.png). 사용자 제공 파란 C 아이콘을 바탕으로 흰 배경을 투명 처리한 파생본이며 양 테마에서 같은 파일을 사용한다.
- 원본 아이콘: [원본](references/canvanity-mark-original.png). 변경 없이 보존한다.
- 색상 참고: [캔버스 예시](references/canvas-color-reference.png). 이 이미지는 색상 참고이며 실제 구현 화면이나 서비스 콘텐츠가 아니다. 예시 페이지 구성은 이번 작업 범위에 포함하지 않는다.
- 공개 설정: 루트 project.json의 logo. make project-brand가 ignored frontend/project.local.json과 public/project-brand/logo.png를 생성한다. env·시크릿을 수정하지 않는다.
- 적용: 기존 BrandMark/BrandBanner를 사용하는 헤더·사이드바·인증·쇼케이스, 브라우저 파비콘과 구성된 공유 메타데이터. 네이티브 아이콘 소스도 같은 C 마크로 생성한다.

## 색상

공통 색상은 src/frontend/src/styles/app.css의 기존 토큰이 소유한다. 명시적 다크와 OS 자동 다크는 같은 색상값을 사용한다.

| 용도 | 라이트 | 다크 |
| --- | --- | --- |
| 바탕 | #f8fbff | #0d1420 |
| 사이드바 | #eef5ff | #121e2e |
| 본문 | #142033 | #eaf2ff |
| 강조 | #2672d8 | #8cbcff |
| 기본 버튼 / 글자 | #2368c7 / #ffffff | #8abaff / #0c203a |
| 버튼 hover | #1b58ac | #a6cbff |

참고 화면의 밝은 파랑을 표면·선택·포커스·정보 상태에 반영하고, 작은 텍스트와 버튼은 대비를 확보하도록 조정한다. 오류·경고·성공의 의미 색상은 유지한다. 기존 크기·간격·라우트·저장소 키·상태 소유자는 변경하지 않는다.

## 파생본 생성 기록

기본 imagegen 편집 도구를 사용했다. 최종 편집 지시: 원본 C의 형태·기울기·그라데이션을 유지하고 흰 배경만 실제 투명 알파로 제거한다. 정사각형 여백을 남기고 텍스트·타일·테두리·그림자·추가 요소를 넣지 않는다. 원본과 파생본을 구분해 보존한다.

네이티브 PNG/ICO/ICNS는 Tauri icon 도구로 실사용 PNG에서 생성한다. 아이콘 소스 대치는 네이티브 패키지 빌드/서명/설치 검증을 의미하지 않는다. 제3자 제공자 아이콘과 과거 worklog/원본 스크린샷은 변경하지 않는다.
