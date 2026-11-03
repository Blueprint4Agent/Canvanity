# Content Canvas 객체 스키마 v1

관련 이슈: [#5 객체·문서 설계](https://github.com/Blueprint4Agent/Canvanity/issues/5), [#7 문서 저장](https://github.com/Blueprint4Agent/Canvanity/issues/7). [설계 진입점](README.md)

## 현재 적용 범위

2026-11-03에 게시글 Canvas의 객체 타입과 문서 내부 검증을 `app/models/canvas.py`의 `CanvasContent`로 구체화했다. 기존 `list[dict]`를 Text/Image/Drawing/Shape/Edge 모델로 바꾸고 기존 문서 GET 응답의 OpenAPI·생성 타입에 반영한다. 기본 초안은 종전과 동일한 빈 문서다.

현재 본문 PUT·revision CAS·실제 에셋 조회/참조 갱신·제품 편집기는 구현하지 않았다. 객체 스키마 확정과 저장 기능 완료를 구분한다. #7에서 현재 작성자/역할/등급·Board/Shelf 상태와 에셋을 검사하고 문서 저장·revision·이미지 참조를 원자적으로 연결한다. Board 공식 홈의 `widgets`는 #25의 별도 스키마다.

## 문서와 객체

| 문서 필드 | 의미·제약 |
| --- | --- |
| `schema_version` | 정수 `1`. 문자열·boolean·알 수 없는 버전을 받지 않는다. |
| `engine` | `name=excalidraw`, `version=0.18.1`, 정수 `adapter_version=1`만 지원한다. |
| `settings` | `background`, `grid`, `width`, `height`. 기본 `#F8F7F4`/`dots`/3200/2100. |
| `nodes` | `type`으로 구분한 `text`/`image`/`drawing`/`shape` 배열. |
| `edges` | `type=edge`. 자유 선 또는 노드에 연결된 화살표 배열. |
| `element_order` | 모든 node/edge ID를 정확히 한 번 포함하는 아래→위 레이어 순서. |

공통 객체 필드는 `id`, `type`, `position:{x,y}`, `size:{width,height}`, `engine_element`다. ID는 길이 1~80 문자열이고 노드와 연결선 전체에서 유일하다. `position`/`size`와 엔진의 `x`/`y`/`width`/`height`, 바깥 ID와 엔진 ID는 일치해야 한다. 조용한 보정·자동 ID 교체·요소 삭제를 하지 않는다.

바깥 문서/API 필드는 `snake_case`다. `engine_element` 내부만 고정 엔진의 원래 필드명(`strokeColor`, `fontSize` 등)을 그대로 사용한다. 카메라·선택·커서·undo stack·파일 바이너리·URL은 문서에 넣지 않는다. 모든 중첩 모델에서 알 수 없는 필드를 거부하고 숫자 문자열·boolean을 좌표나 정수로 변환하지 않는다.

## 타입별 데이터

| 객체 | 바깥 필드 / 엔진 타입 | 실제 내용 |
| --- | --- | --- |
| Text | `type=text`, 엔진 `type=text` | `engine_element.text`·`originalText`의 plain text, 글꼴/크기/정렬/줄높이. 별도 `content.text`에 중복 저장하지 않는다. |
| Image | `type=image`, `content:{asset_id:UUID}`, 엔진 `type=image` | 서버 Asset 식별자만 저장한다. `fileId`·바이너리·서명 URL은 제외한다. |
| Drawing | `type=drawing`, 엔진 `type=freedraw` | 로컬 좌표 `points`, 0~1의 `pressures`, `simulatePressure`. |
| Shape | `type=shape`, 엔진 `type=rectangle\|ellipse\|diamond` | 도형 종류·채움·외곽선·회전·모서리 속성. |
| Edge | `type=edge`, `source_node_id`·`target_node_id`, 엔진 `type=line\|arrow` | 끝점·제어점·화살촉·바인딩. 자유 끝점은 `null`. |

본문 예시/회귀 입력은 [실제 엔진 export fixture](../../src/backend/tests/fixtures/canvas_content_v1.json)를 사용한다. Excalidraw 0.18.1을 React 독립 검증 화면에서 export한 5요소이며 Asset ID를 문서 계약용 UUID로 바꾸고 seed/version/nonce/updated를 고정했다. 이 UUID는 실제 업로드된 에셋이 아니다. 이 작업은 제품 편집기 채택·실기 입력 검증 완료를 뜻하지 않는다.

## 고정 엔진 필드

엔진의 [고정 v0.18.1 타입](https://github.com/excalidraw/excalidraw/blob/v0.18.1/packages/excalidraw/element/types.ts)·[글꼴/스타일 상수](https://github.com/excalidraw/excalidraw/blob/v0.18.1/packages/excalidraw/constants.ts)와 실제 export를 기준으로 허용 목록을 정했다. 아래 필드 외의 `link`·`customData`·실행/Embed 관련 데이터는 통과시키지 않는다.

| 구분 | 필드·정책 |
| --- | --- |
| 공통 기하 | `id,type,x,y,width,height,angle`. 모든 실수는 유한값. |
| 공통 스타일 | `strokeColor,backgroundColor,fillStyle,strokeWidth,strokeStyle,roundness,roughness,opacity`. |
| 엔진 메타데이터 | `seed,version,versionNonce,index,updated,locked`. 정수 범위와 index 길이를 제한한다. `version`은 엔진 요소 버전이며 서버 문서 revision과 별개다. |
| 그룹/프레임/삭제 | `groupIds=[]`, `frameId=null`, `isDeleted=false`만. 삭제 요소는 export 전에 제거한다. Group/Frame은 후속이다. |
| 역참조 | `boundElements`는 `null` 또는 `{id,type:arrow\|text}` 목록. 중복·dangling·한쪽만 연결된 참조를 거부한다. |
| Text 추가 | `text,originalText,fontSize,fontFamily,textAlign,verticalAlign,containerId,autoResize,lineHeight`. 글꼴 ID는 고정 버전의 1/2/3/5/6/7/8/9. |
| Image 추가 | `status=saved,scale,crop`. scale 각 축은 정수 -1/1. crop은 x/y/width/height/naturalWidth/naturalHeight이며 원본 크기 안에 있어야 한다. |
| Drawing 추가 | `points,pressures,simulatePressure,lastCommittedPoint=null`. 필압 길이는 점 수와 같아야 하며 simulatePressure=true일 때 빈 필압 배열도 허용한다. |
| Line/Arrow 추가 | `points,lastCommittedPoint=null,startBinding,endBinding,startArrowhead,endArrowhead`. Arrow는 `elbowed=false`만. Line의 노드 바인딩과 꺾인 화살표/fixedSegments는 이번 버전에 포함하지 않는다. |

색은 3/6/8자리 hex 또는 `transparent`, 채움은 hachure/cross-hatch/solid/zigzag, 외곽선은 solid/dashed/dotted만 허용한다. 외곽선 두께 0~1,000, roughness 0~10, opacity 0~100이다. roundness는 고정 엔진의 type 1/2/3과 선택적 value를 갖는다. Text의 fontSize는 0 초과~10,000, lineHeight는 0 초과~10이다. seed/versionNonce는 0~2³¹−1, version은 1~2⁵³−1, updated는 0~2⁵³−1이다. index는 null 또는 길이 1~128 문자열이고 영속 레이어 순서는 `element_order`가 기준이다.

## 연결·포함·레이어 불변식

- `element_order`에서 ID 누락·추가·중복을 거부한다. nodes/edges 배열을 나눠도 전체 순서를 보존한다.
- 연결된 화살표의 source/target은 같은 문서의 Text/Shape/Image 노드만 가리킨다. Drawing·다른 Edge·없는 ID는 대상이 될 수 없다.
- `source_node_id`/`target_node_id`와 엔진 `startBinding`/`endBinding.elementId`가 일치해야 한다. 엔진 바인딩에는 elementId/focus(-1~1)/gap(0~100,000)만 허용한다.
- 대상 노드의 `boundElements`에도 그 화살표가 있어야 한다. 자유 끝점의 엔진 바인딩은 null이다.
- Text의 `containerId`는 같은 문서의 Shape 또는 Arrow다. 컨테이너의 text 역참조가 일치해야 하며 한 컨테이너에 bound text는 최대 1개다. 그룹/프레임을 이 필드로 대신하지 않는다.
- `boundElements`의 대상 타입과 실제 객체 종류, 순방향 참조가 서로 일치해야 한다.

이 검사에는 DB 조회가 필요하지 않다. 다른 Canvas/Board의 asset_id, pending/deleting 에셋, 현재 정책/역할/등급은 구조만으로 판단하지 않고 #7의 저장 트랜잭션에서 검사한다.

## 제한과 실패 처리

| 항목 | v1 제한 |
| --- | --- |
| 문서 | 검증한 모델을 compact UTF-8 JSON으로 직렬화했을 때 최대 2 MiB |
| 요소 수 | nodes+edges 합계 최대 2,000개 |
| 위치·로컬 점·angle | 유한수, 절댓값 최대 100,000 |
| 크기 | 각 축 0~100,000. Text/Image/Shape는 양수, Drawing/Edge는 한 축 0 허용·두 축 모두 0 거부 |
| 세계 크기 | width/height는 1~100,000의 엄격한 정수 |
| 텍스트 | text/originalText 각각 최대 20,000자, 유효한 UTF-8 |
| 경로 | Drawing당 1~20,000점, Edge당 2~20,000점. 각 점은 길이 2 배열 |
| 이미지 | content.asset_id는 UUID. 실제 형식/바이트/픽셀·소유 검사는 Asset API·저장 트랜잭션 책임 |

수치는 입력 거부 상한이며 렌더링·저장 성능 보장이 아니다. 이 바이트 제한은 원시 HTTP 요청 길이와 다르다. #7은 JSON 디코딩 전 요청 크기 제한과 인증/권한 경계도 별도로 적용해야 한다.

스키마/엔진/어댑터의 알 수 없는 버전이나 위반 데이터는 모델 검증 오류로 거부한다. 앞으로 입력 PUT이 연결되면 422로 응답하며 현재 미구현 경로를 공개 API처럼 설명하지 않는다. 버전 변경은 명시적 변환과 회귀 fixture가 필요하고 자동으로 버전을 올리거나 손실 변환하지 않는다. `DOCUMENT_UPGRADE_REQUIRED` 등 읽기 전용 전환 계약은 실제 이관 구현 때 연결한다.

## 검증과 다음 단계

실제 엔진 5타입 fixture의 한글·좌표·이미지 UUID·순서 JSON 왕복, 기존 빈 문서 호환과 GET 직렬화, 잘못된 버전/타입/숨은 필드/NaN·무한수/참조·기하·UTF-8 크기, 요소/텍스트/점 수 경계를 회귀로 확인한다.

다음 #7은 이 모델을 PUT 입력으로 재사용하고 기대 document revision의 원자적 CAS, 현재 권한 재검사, 문서와 draft 에셋 참조 갱신을 같은 트랜잭션에 연결한다. 저장 후 GET 왕복·실제 PostgreSQL 경쟁/롤백·정리 경쟁을 그 단계에서 검증한다. 자동 저장/복구 UI와 공개 snapshot은 각각 후속 #7/#8에서 진행한다.
