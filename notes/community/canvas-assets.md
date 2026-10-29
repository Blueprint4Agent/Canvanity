# Canvas 이미지 에셋 — #6

작성자 전용 Canvas 초안의 이미지 업로드·조회·삭제 기반이다. 선행 초안 PR #42의 7631143을 기준으로 한다. 실제 편집기 붙여넣기/드롭·본문 저장·공개 게시 연결은 #7/#8의 후속이며 구현·검증·원격 게시·main 병합은 이슈/PR에서 구분한다.

## API와 접근

모든 경로는 `/api/v1` 기준이며 Bearer 세션 전용이다. API Key는 허용하지 않는다.

| Method | Path | 계약 |
| --- | --- | --- |
| POST | /canvases/{canvas_id}/assets | multipart `file`. 정규화·저장 후 201, Location과 에셋 요약 |
| GET | /canvases/{canvas_id}/assets/{asset_id} | 현재 작성자의 ready 이미지 바이트, image/webp |
| DELETE | /canvases/{canvas_id}/assets/{asset_id} | 미참조 에셋을 deleting으로 바꾸고 정리 예약, 204 |

요약에는 id/canvas_id/content_type/byte_size/width/height/frame_count/state/expires_at/created_at/url만 반환한다. 객체 키·저장 위치·해시·원본 이름은 반환하지 않는다. 성공 응답은 `Cache-Control: private, no-store`, 이미지 응답은 nosniff와 UUID 파일명을 사용한다. 정적 public 디렉터리에 파일을 노출하지 않는다.

CanvasAccessService가 CanvasService와 AssetService의 현재 작성자·멤버·계정·Board/Shelf 검사를 공유한다. Owner/Admin/Moderator와 공개 visibility도 타인 초안에 접근하지 못한다. 탈퇴/pending/제재·정지된 Board는 404다. 다른 Canvas의 에셋 ID도 404다. 업로드는 active Board의 draft와 현재 Shelf 읽기/작성 정책을 요구한다. 읽기는 등급 강등·휴지통·Board 보관 후에도 유효한 작성자에게 허용한다. 미사용 파일 삭제는 등급이 낮아도 가능하지만 보관 Board에서는 변경하지 않는다. 초안·공개본 중 하나라도 참조하면 ASSET_REFERENCED 409다.

## 이미지와 저장 한도

파일명과 요청 MIME을 신뢰하지 않고 실제 PNG/JPEG/WebP/GIF를 디코딩한다. 입력과 정규화 출력은 각각 8 MiB, 누적 디코딩 픽셀은 `width × height × frame_count ≤ 16,000,000`, 최대 100프레임이다. Canvas당 pending/ready/deleting을 합쳐 최대 200개다. EXIF 방향을 적용하고 메타데이터를 제거한 WebP로 저장한다. 투명도와 한도 내 애니메이션을 유지하며 duration은 20~10,000ms로 제한한다. SVG·위장·손상은 422, 바이트 상한은 413이다. 인코더가 동일 프레임을 합치면 실제 출력 프레임 수를 반환한다.

새 불변 키는 `canvas-assets/{asset_uuid}/{random_uuid_hex}.webp`다. DB에는 바이너리 대신 정보·SHA-256·저장 위치 지문을 기록한다. read는 크기/MIME/해시와 실제 바인딩된 저장소를 검증한다. DB/파일 장애는 ASSET_UNAVAILABLE 503으로 변환하고 원문을 응답에 넣지 않는다.

## 업로드와 참조 트랜잭션

1. 현재 접근·작성 정책을 검사하고 이미지를 정규화한다.
2. Board→User 공유 잠금→Canvas 순서로 재검사하고 pending 에셋과 정리 outbox를 **파일 put 전에 한 트랜잭션으로 예약**한다.
3. 트랜잭션을 닫은 뒤 ObjectStorage.put을 실행한다.
4. 현재 권한·draft·업로드 기한을 다시 검사하고 ready와 미참조 만료를 원자 기록한다.

put 실패/취소·권한 회수·후속 DB 실패에도 원래 예약이 남는다. 확인된 ready는 커밋 결과가 불확실해도 보상 삭제하지 않는다. pending 업로드 기한은 1시간이며 실패 보상도 그 기한과 최소 60초 유예를 지킨다. 정리된 뒤 늦게 put이 끝난 경우에는 남겨 둔 완료 기록을 다시 예약할 수 있다. 파일 I/O는 SQL 잠금 밖에서 실행한다.

`assets(board_id,canvas_id)`는 Canvas 복합 키를 참조한다. `canvas_asset_refs`는 draft/publication을 독립적으로 기록하며 같은 Board/Canvas의 **ready 상태**만 복합 FK로 참조한다. 참조가 있으면 expires_at을 비우고 마지막 참조가 사라지면 24시간 유예를 다시 부여한다. deleting/pending·다른 Canvas의 연결은 거부한다. 문서 저장 서비스는 실제 문서를 검증하고 Board/Canvas 잠금 안에서 `replace_refs`를 본문 변경과 함께 호출해야 한다. 현재는 저장소 기반만 구현하며 문서 저장/게시 API를 제공하지 않는다.

## 삭제 outbox와 운영

`asset_deletion_outbox`에는 부모 FK가 없다. 보관 Board 삭제는 같은 DB 트랜잭션에서 모든 에셋의 원래 위치·키를 기록하고 참조→에셋→본문→Canvas→Shelf를 정리한다. 실패하면 전부 롤백한다. User/다른 Board/프로필 파일을 삭제 대상으로 추측하지 않는다.

워커는 pending 또는 lease가 만료된 processing을 조회해 현재 참조와 위치를 확인한다. 다른 에셋·초안/공개본·기존 프로필 참조가 같은 키를 사용하면 보호한다. 저장소 지문 불일치는 blocked이며 DB에 저장된 위치로 임의 클라이언트를 만들지 않는다. ready→deleting 전환과 10분 lease/token을 커밋한 후 파일을 삭제한다. 이전 token의 늦은 완료는 무시한다. 실패는 60초부터 최대 1시간의 backoff로 5회까지 재시도한 뒤 dead로 보관한다. 허용된 Canvas 키 형식만 삭제한다.

Celery task `canvanity.assets.cleanup`를 singleton Beat가 60초마다 발행한다. API·워커·Beat는 같은 DB와 원래 ObjectStorage 설정을 사용해야 한다. local이면 같은 볼륨을 공유한다. 실행 안내는 [CELERY.md](../../src/backend/CELERY.md)와 [ObjectStorage](../object-storage.md)를 따른다. 별도 워커가 없으면 다음 CLI로 같은 정리를 수행할 수 있다.

```bash
cd src/backend
uv run python -m app.manage_asset_cleanup --limit 20
uv run python -m app.manage_asset_cleanup --limit 20 --retry-id <outbox-uuid>
```

CLI는 완료/실패/건너뜀 수와 조치할 작업 ID·상태·시도·안전한 오류·위치 지문을 출력한다. 정상적인 본문 참조 보호는 경고 대상에서 제외한다. 원래 설정을 복원한 뒤 blocked/dead 작업을 재처리한다. 활성 lease는 수동 재처리로 덮어쓰지 않는다. 완료 tombstone도 재처리할 수 있어 뒤늦은 객체 복원/put을 정리한다. 비밀키는 env에만 두며 위치 기록에는 provider/root 또는 endpoint/bucket/region만 들어간다. 앱 시작 시 실제 클라이언트와 위치를 함께 고정하므로 실행 중 전역 설정만 바뀌어도 다른 위치로 오인하지 않는다. DB 연결은 기존 설정처럼 DB_DRIVER/DB_NAME/DB_HOST 등으로 구성한다.

1시간/24시간은 정리 대상 시각이며 물리 삭제 SLA가 아니다. 워커 중단·원격 장기 지연·버전 보관 정책에 따라 삭제가 늦어질 수 있다. 원격의 이전 버전까지 제거하거나 기한 이후 완료되는 모든 put을 차단하지는 않는다. DB/파일을 함께 복원하고 완료 tombstone을 유지해 필요한 재처리를 수행한다. 프로필 사진의 기존 best-effort 정리를 이 outbox 보장으로 확대하지 않는다.

0027 migration은 기존 SQLite Canvas를 재생성하지 않고 복합 유니크 인덱스를 추가한다. downgrade는 에셋이 남거나 미완료 outbox가 있으면 거부한다. 참조 해제·정리 완료 후에만 실행해 유일한 파일 정리 기록을 잃지 않게 한다.
