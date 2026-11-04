# Board 대표 이미지와 커버 — #59

Board 소유의 avatar/cover를 현재 운영 권한·Board revision과 연결한다. Canvas 전용 `assets`와 프로필 사진은 별도 수명주기를 유지한다. [#59](https://github.com/Blueprint4Agent/Canvanity/issues/59)의 실제 검증·ready PR·main 병합은 [worklog0298](../../worklog/0298-board-media.md)과 이슈/PR에서 구분한다. 업로드/크롭 편집 UI·썸네일·제공자 설정·운영 배포는 후속이다.

## HTTP 계약

모든 경로는 `/api/v1` 기준이다. slot은 `avatar|cover`만 허용한다.

| Method | Path | 계약 |
| --- | --- | --- |
| PUT | /boards/{board_id}/media/{slot} | multipart file/expected_revision/reason. 검증·예약·put 후 현재 선택, 200과 Location. |
| GET | /boards/{board_id}/media/{slot}/{asset_id} | 현재 선택된 ready 버전만 image/webp 바이트. |
| DELETE | /boards/{board_id}/media/{slot} | JSON expected_revision/reason. 논리적 선택 해제, 실제 파일은 outbox 정리, 200. |

변경 응답은 `{board_id,slot,media,board_revision,changed}`다. media는 id/content_type/byte_size/width/height/frame_count/created_at/상대 API url만 포함한다. 객체 키·위치·지문·해시·원본 이름·서명 URL을 응답/layout/감사에 복제하지 않는다. 모든 성공 응답은 `Cache-Control: private, no-store`, 이미지에는 `X-Content-Type-Options: nosniff`와 UUID 파일명을 적용한다.

reason은 공백 제거 후 1~500자다. DELETE revision은 strict JSON 정수 0~2,147,483,647이며 bool/float/문자열을 거부한다. multipart revision은 전송상 문자열이므로 ASCII 숫자 1~10자리만 정수로 파싱한다. 음수·부호·공백·지수·소수·bool·범위 초과는 422다.

PUT은 파싱 전 encoded 본문을 **8MiB+64KiB**, multipart를 파일 최대1개/텍스트 필드 최대2개/각 텍스트 part 최대2048바이트로 제한한다. 개수·텍스트 part 한도는 HTTP400 `{detail:string}`, encoded/파일 바이트 한도는 413 `ASSET_TOO_LARGE`, 필수 필드/slot/revision/reason 검증은422다. 이 파서는 GET/DELETE에는 적용하지 않는다. 전송 파싱 뒤 서비스가 현재 권한/CAS를 검사한 다음 파일 바이트를 읽고 디코딩한다.

## 현재 권한과 revision

PUT/DELETE는 Bearer 세션과 현재 활성 계정, active Board의 active Owner/Admin을 요구한다. Moderator·Curator/등급·앱 전역 admin·다른 Board 운영 역할·API Key는 변경 권한을 부여하지 않는다. 홈의 `can_manage_media`는 변경 API와 같은 공개 권한 가드에서 계산한다. archived에서는 읽기만 가능하며 변경은403이다. suspended Board/제재는404다.

GET은 optional Bearer로 현재 Board 공개/회원/제재/계정 정책을 적용한다. API Key만 있으면 익명이고 잘못된 Bearer는401이다. private의 비회원/pending/탈퇴·제재·정지, 다른 Board/slot, Canvas Asset, pending/deleting/이전 이미지 UUID는404다. 로그인 계정 상태는 기존 인증 의존성의 현재 검사도 적용한다. 바이트 조회 전 snapshot에서 현재 ref/권한을 확인하고 저장소 I/O 뒤 새 snapshot으로 다시 확인한다. 이미 전달한 이미지의 회수는 보장하지 않는다.

공용 `boards.revision INTEGER32`로 CAS한다. 사전검사·pending 예약·ready 선택 직전에 기대 revision을 확인한다. 예약은 Board revision/선택/감사를 바꾸지 않는다. 최종 선택·교체/제거만 revision을1 증가시키고 `media_changed` 감사와 outbox를 원자 반영한다. 같은 바이트를 다시 올려도 새 UUID/새 변경이다. 같은 기대 revision의 동시 업로드는 최종 선택 한 개만 성공하고 나머지는409다. 중간 설정/회원 역할/Board 상태 변경도 최종 검사에 반영한다.

빈 slot DELETE는 기대값 검사 후 `changed:false`이며 revision/감사는 유지한다. stale는409 `BOARD_REVISION_CONFLICT`, 실제 변경 시 포화는409 `BOARD_REVISION_EXHAUSTED`다. 상한의 빈 slot no-op은 허용한다. layout/document/publication revision은 변경하지 않는다. 감사는 slot/이전·새 asset UUID/전후 revision/reason만 저장하며 member-audit의 typed `media_change`에 허용 필드만 노출한다.

## DB 소유와 이미지

`0030_board_media`는 기존 부모/Canvas Asset/outbox를 ALTER하거나 SQLite 부모 테이블을 재생성하지 않고 두 테이블만 추가한다.

- `board_media_assets`: Board FK RESTRICT, 업로더 FK SET NULL, slot·private object 정보·실제 정규화 metadata·SHA256·pending/ready/deleting·1시간 업로드 기한.
- `board_media_refs`: `(board_id,slot)` PK와 `(board_id,slot,asset_id,asset_state)` 복합 FK/ready CHECK. 같은 Board·slot의 ready만 선택하며 assets의 target UNIQUE와 FK 인덱스를 둔다.

Board의 avatar_asset_id/cover_asset_id는 응답용 현재 ref projection이며 boards의 nullable soft UUID 저장 컬럼이 아니다. 기존 `assets.canvas_id` 필수·same Canvas ready FK를 유지한다. 다른 Canvas/private 파일/임의 외부 URL은 Board 이미지로 연결하지 않는다.

기존 순수 이미지 정규화를 공유한다. 파일명/MIME을 신뢰하지 않고 PNG/JPEG/WebP/GIF를 실제 디코딩해 EXIF 방향 적용·메타데이터 제거 WebP로 저장한다. 입력/출력 각각8MiB, 누적16,000,000 pixels, 최대100프레임이며 투명도/한도 내 애니메이션을 유지한다. Board별 pending 최대8개, 전체 등록 최대200개(ready/삭제 대기 포함)다. 한도는409 `BOARD_MEDIA_LIMIT_REACHED`이며 정리를 진행한 뒤 재시도한다.

새 키는 `board-media/{asset_uuid}/{random_32hex}.webp`다. 읽기는 고정된 현재 저장소의 descriptor/fingerprint와 실제 key/size/MIME/SHA256을 검증한다. DB 기록으로 임의 저장소 클라이언트를 만들지 않는다. 저장소 장애/무결성 불일치는503이며 내부 경로나 원문 오류를 응답하지 않는다.

## 파일 I/O와 정리

현재 권한/CAS → 파일 읽기/정규화 → Board FOR UPDATE·활성 User FOR SHARE 재검사 → pending+parentless outbox 예약 commit → 트랜잭션 밖 put → 같은 현재 권한/CAS·기한 재검사 → 정렬한 새/이전 media 잠금·ref 교체/ready·감사·outbox commit 순서다. ref 해제를 먼저 flush해 RESTRICT 대상 ready를 이후 deleting으로 바꾼다. 모든 파일 I/O는 SQL 트랜잭션 밖이다.

put 실패/취소·권한 회수·최종 flush/commit 실패는 shield 정리 의도를 유지한다. 최종 commit 결과가 불명확해도 확인된 ready는 보상 삭제하지 않는다. 실패한 pending은 원래1시간 기한과 최소60초 settle을 지켜 늦은 put을 수습한다. 실패 보상으로 pending이 이미 deleting이 된 뒤 Board를 삭제해도 기존 upload_pending/upload_failed deadline/settle을 앞당기지 않는다. 사용하지 않은 ready 상태는 외부에 선택되지 않으며 교체/제거된 이전 ready는 deleting/즉시 outbox가 된다. uploader 계정 삭제는 SET NULL이며 소유권 이전도 커뮤니티 미디어를 유지한다.

기존 [Canvas cleanup](canvas-assets.md)의 worker/Beat/CLI를 함께 사용한다. outbox의 strict `canvas-assets|board-media` namespace로 등록부를 결정하고 허용 키/asset UUID·Board/key/fingerprint/descriptor 일치와 두 등록부의 같은 key/fingerprint·Canvas draft/publication/현재 Board ref·프로필 참조를 검사한다. 다른 등록부는 같은 UUID여도 별도 객체이므로 UUID만으로 제외하지 않는다. 같은 UUID지만 다른 key인 Canvas 참조는 무관한 Board orphan을 영구 보호하지 않는다.

worker는 실제 위치 descriptor를 항상 전달한다. legacy 직접 `claim(job, fingerprint)` 호출은 fingerprint 바인딩 호환 경로이며 candidate/job의 descriptor 일치는 여전히 확인한다. 운영 worker/CLI는 이 생략 경로를 사용하지 않는다. invalid key/asset mismatch/location mismatch는 파일 delete 전 blocked이며 실행 카운터는 skipped다. 다른 살아있는 ref는 protected다. 부모가 이미 삭제된 정상 job도 strict key/현재 위치/교차 참조를 검사한 뒤 정리할 수 있다.

claim/finish/실패 보상은 Board→해당 Asset→outbox, Board 삭제는 Board→정렬 Board media→outbox→기존 Canvas assets 순서다. Board 영구 삭제는 모든 current/이전/pending refs와 등록부를 같은 트랜잭션에서 정리하고 원래 key/location을 FK 없는 outbox에 남긴다. 10분 lease/token fencing, 5회 backoff(60초~1시간), blocked/dead/done 기록과 완료 tombstone 재예약을 유지한다. 삭제·cleanup/늦은 put 경쟁에서도 정상 current ready를 지우지 않는다. 기한은 물리 삭제 SLA가 아니다.

## 요약과 마이그레이션 운영

Board 목록/상세/by-slug/home/설정 응답은 현재 avatar/cover UUID·요약을 제공한다. 목록은 계정/현재 권한/Board revision/Interest와 media batch를 PostgreSQL REPEATABLE READ READ ONLY/SQLite BEGIN snapshot으로 묶어 N+1과 혼합 버전을 피한다. 홈도 기존 snapshot의 batch를 사용하며 실제 board_cover.widget_data.media는 같은 summary.cover 또는null이다. 저장 layout의 source/asset_id/URL 금지는 유지한다.

downgrade는 새 등록부/ref 또는 board-media outbox 기록(완료 tombstone 포함)이 남으면 거부한다. 자료와 정리 이력을 내보내고 운영자가 별도 정리 절차를 결정해야 하며 자동 삭제/fallback은 없다. 신규 기록이 전혀 없을 때만0029로 돌아갈 수 있다. 테스트는 FK 활성 SQLite·고유 PostgreSQL schema에서0029의 Board/회원/layout/Canvas/document/publication/counter/Tag/Asset/ref/비어있지 않은 outbox lease/token/location 및 프로필·다른 Board 보존을 확인한다. 원본 개발 DB/env/파일과 실제 제공자는 테스트 대상이 아니다.
