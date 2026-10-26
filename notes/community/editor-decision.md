# Content Canvas 편집 엔진 검토

2026-10-26, [#4](https://github.com/Blueprint4Agent/Canvanity/issues/4) 기술 검증. [설계 진입점](README.md)

## 결정

**Excalidraw 0.18.1을 MVP Content Canvas의 우선 검증 후보로 선택한다.** React 18.3.1과 실제 독립 브라우저에서 입력·그리기·이미지·문서 복원을 검증했다. 제품 의존성/라우트에는 추가하지 않았다. 제품 채택 완료는 OS 한국어 IME·실기 펜/터치·유한 카메라/공용 단축키 통합·대표 이미지 부하 검증까지 통과한 뒤 판단한다.

Board/Plaza의 UI Canvas는 기존 DOM 위젯+CommunityCanvas/ExploreCanvas/useCanvasCamera를 사용한다. Excalidraw로 Board 위젯을 다시 구현하지 않는다. 두 화면은 데이터 책임을 분리하고 좌표·카메라 정책과 액션 의미만 맞춘다.

## 후보 비교와 근거

| 후보                          | 기능 적합성                                         | 호환/배포 조건                            | 판단                                                                                 |
| ----------------------------- | --------------------------------------------------- | ----------------------------------------- | ------------------------------------------------------------------------------------ |
| @excalidraw/excalidraw 0.18.1 | Text/Image/FreeDraw/Shape/Arrow·undo/redo·scene API | npm peer React 17/18/19, 해당 tag MIT     | 독립 실행 후보. 한국어/이미지·복원·스타일 통합 비용 실측                             |
| tldraw SDK                    | 완성도 높은 캔버스·커스텀 shape/확장                | 공식 문서상 production license key 필요   | 라이선스/운영 조건을 추가로 결정해야 하므로 이번 MVP 기본 의존성으로 넣지 않음       |
| React Flow                    | 노드/연결선·커스텀 UI·graph 적합                    | freehand는 공식 whiteboard 구현 예제 제공 | 게시글 자유 드로잉/텍스트/이미지 UX의 자체 구현 범위가 더 커 이번 우선 후보에서 제외 |

라이선스/React peer는 실제 설치한 npm package와 고정 tag를 확인했다. 엔진 내 폰트·하위 의존성 라이선스도 제품 배포 시 고지에 포함한다. MIT 상위 라이선스가 모든 번들 자산의 동일 라이선스를 의미하지 않는다. tldraw/React Flow는 문서 비교만 했고 동일 성능 fixture를 실행했다고 표현하지 않는다.

## 독립 검증 화면

[package.json](probes/editor/package.json)과 [lockfile](probes/editor/package-lock.json)을 제품 의존성과 분리했다. [화면](probes/editor/main.mjs), [어댑터](probes/editor/adapter.mjs), [브라우저 검사](probes/editor/check.mjs)는 `127.0.0.1:5193`에서 실행한다. [재현 절차](development-validation.md)를 따른다. 패키지를 다운로드하는 설치 단계 외에 테스트는 외부 제공자가 필요하지 않다. 데스크톱 검사에서는 외부 HTTP 요청을 차단하고 로컬 폰트 경로를 사용한다.

검증 내용:

- text/image/drawing/shape/edge 5요소의 순서·텍스트·좌표·필압 배열·asset 참조를 canonical JSON으로 직렬화/복원하여 비교한다.
- 한국어 두 줄과 `/ v +`를 실제 텍스트 편집 DOM에 입력하고 저장·복원한다. 합성 composition 이벤트 전달도 검사한다. **OS 네이티브 IME 조합 성공을 입증하는 검사는 아니다.**
- 마우스 포인터 freehand와 keyboard undo/redo를 확인한다.
- 브라우저 파일 드롭·clipboard paste를 합성하고 이미지 요소가 생성되는지 확인한다. 바이너리는 엔진 메모리에만 존재한다.
- canonical JSON을 localStorage에 저장하고 페이지 reload 후 복원·동등성을 확인한다. 실제 서버/DB/오브젝트 스토리지 round-trip과 구분한다.
- 100/1,000요소 fixture에서 갱신→두 animation frame, encode, restore→두 frame 시간을 관측한다. FPS/입력 응답시간·대규모 이미지 성능으로 설명하지 않는다.
- 390×844 touch context에서 렌더링·tap과 5요소 보존을 확인한다. 실제 휴대폰 pinch/pan·키보드·펜 필압은 미검증이다.

## 복원 실패 조사와 수정

초기 skeleton을 바로 updateScene에 넣으면 FreeDraw 기본 속성과 Arrow 좌표가 restoreElements에서 정규화됐다. seed도 엔진 restore 경로를 통과하도록 바꿨다. 이어 비교에서 optional `customData: undefined` 같은 JS 전용 필드가 JSON 왕복 후 사라지는 차이를 발견했다. canonical 생성 시 JSON 값으로 정리하여 저장 전/후 계약을 맞췄다. 요소 순서·좌표·텍스트·points·pressure·파일 ID의 비교는 유지했다.

debug-live breakpoint/start를 시도했지만 디버거 세션이 생성되지 않아 stop/clear로 정리하고, 별도 Playwright의 브라우저 evaluate로 복원 전후 문서 값만 검사했다. 제품 코드에 로그를 추가하지 않았다. 수정 후 최종 결과와 한계는 아래 실측 기록을 따른다.

## 최종 실측 기록

브라우저 검사 9개가 모두 통과했다. 1440×1000 화면에서 한글·도형·화살표·그리기·이미지 fixture, 390×844에서 툴바·한글·도형 표시를 시각 확인했다. 모바일에서는 세계 일부만 표시되므로 제품에서는 유한 카메라/fit 통합이 필요하다.

| 요소 수 | JSON bytes | encode | restore→두 frame |
| ------- | ---------- | ------ | ---------------- |
| 100     | 54,672     | 0.5ms  | 16.4ms           |
| 1,000   | 543,687    | 5.5ms  | 42.8ms           |

로컬 단일 실행의 관측이며 반복 통계/제품 SLA가 아니다. 고정 개수·배치에 엔진 seed/시각 필드가 포함되어 JSON byte 크기는 실행마다 소폭 달라질 수 있다. 의존성 고정 production build도 통과했다. 최대 약 1.82MB minified chunk(약 737KB gzip)와 500KB 초과 chunk 경고, 하위 패키지의 use-client 지시자 무시 경고가 있다. 제품에서는 편집 경로 지연 로딩·폰트 self-host와 실제 production runtime을 별도 확인한다. 독립 build 성공은 제품 번들 크기 증가나 배포 검증 결과가 아니다.

## 문서 어댑터 계약

```text
schema_version / engine(name,version,adapter_version)
settings(background,grid,width,height)
nodes(text,image,drawing,shape)
edges(edge, source_node_id?, target_node_id?)
element_order(전체 node/edge id를 한 번씩 포함)
```

각 요소는 id/position/size와 고정 엔진 버전의 `engine_element`를 가진다. 굽은 선·텍스트 baseline·선 스타일·pressure·바인딩·seed 등은 typed engine_element로 손실 없이 보존한다. z순서는 nodes/edges를 분리해도 element_order로 유지한다. engine_element는 임의 JSON 통과 경로가 아니며 **제품 서버에서 허용 타입/필드/배열/유한수·좌표 일치·참조를 별도로 검증해야 한다.** frame/embed/iframe/custom 실행 필드와 알 수 없는 속성은 거부한다.

image는 `content.asset_id`만 영속화하고 엔진 fileId와 바이너리 매핑은 로드 시 생성한다. probe의 `probe-asset-*`는 메모리 파일 연결을 확인하기 위한 논리 키이며 제품 UUID/Asset API 계약이 아니다. text는 초기에는 plain text, Markdown/리치 텍스트는 후속 확장이다.

비연결 화살표/선은 source_node_id/target_node_id=null을 허용한다. 값이 있으면 현재 문서의 node만 참조하고 engine binding과 일치해야 한다. zero-height/width 선과 점 stroke를 지원하므로 각 축은 0 이상, 둘 다 0인 요소는 거부한다. 일반 shape/image는 양수 크기다. 중복 ID·잘못된 참조·element_order 누락/중복은 422다.

버전 조합은 현재 excalidraw=0.18.1, adapter=1만 허용한다. 엔진 최신 버전으로 자동 저장하지 않고 명시 migrator·fixture round-trip 후 이관한다. 서버 JSONB 본문과 외부 객체 저장소를 분리하며 선택·카메라·커서·undo stack은 저장하지 않는다. undo 이력은 재열기하면 초기화되며 영구 편집 이력이 아니다.

## 제품 적용 전 남은 검증

- OS 한국어 IME 조합 중 단축키·줄바꿈·paste, 실제 펜 pressure·터치 pinch/pan과 스크롤 충돌.
- 실제 OS 이미지 clipboard paste, 여러 파일/대용량 이미지, 선택·이동·크기·레이어 순서의 실제 UI 왕복.
- 공용 CANVAS_RULES(0.25~2 줌·유한 bounds·작은 경계 저항)와 엔진 자체 카메라의 충돌 없는 연결. 현재 독립 화면의 무한 팬을 제품 기본값으로 채택하지 않는다.
- 실제 대표 이미지 fixture의 메모리·decode·렌더·저장 부하, 필요 시 이미지 lazy load.
- 제품 테마/툴바·접근성·계정 전환/저장 충돌, 지연 로딩 chunk와 self-host font 경로의 production runtime 검증.

이 검증들이 남아 있으므로 #4 전체 완료로 처리하지 않는다. Board/Shelf/멤버십 모델 구현은 엔진의 UI 통합 검증과 독립적으로 진행할 수 있다.

## 공식 자료

- [Excalidraw integration](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/integration), [restore/export utilities](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api/utils), [0.18.1 MIT license](https://github.com/excalidraw/excalidraw/blob/v0.18.1/LICENSE).
- [tldraw production license key](https://tldraw.dev/sdk-features/license-key), [license](https://tldraw.dev/community/license).
- [React Flow freehand whiteboard example](https://reactflow.dev/examples/whiteboard/freehand-draw).
