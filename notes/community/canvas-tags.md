# 자유 Tag 사전과 Canvas 연결 — #49 / #24

공식 Interest와 별도로 전역 자유 Tag를 검색·생성하고 Canvas 초안 메타데이터에 연결한다. [#49](https://github.com/Blueprint4Agent/Canvanity/issues/49)는 백엔드 완료 단위다. 구현·검증·PR 게시·main 병합은 이슈/PR에서 구분한다. 태그 입력 UI·추천·Board 자유 Tag·공개 목록은 #24/#8의 후속이다. [게시 단건 계약](canvas-publication.md)은 게시 당시 태그 ID/최초 표시명/순서를 별도 snapshot 관계에 고정한다.

## 이름과 재사용

Tag는 UUID v4, 최초 표시명 `name`, 고유 비교 키 `normalized_name`을 저장한다. 이름은 다음 순서로 검사한다.

1. 원본 문자열이 UTF-8로 인코딩 가능하고 Unicode 제어(Cc)·포맷(Cf)·서로게이트(Cs) 문자를 포함하지 않아야 한다. 탭·개행·NUL·zero-width space도 거부한다.
2. NFC로 정규화하고 Unicode 앞뒤 공백을 제거한 표시명을 1~40자로 제한한다. 내부 공백은 보존한다.
3. 표시명을 casefold한 뒤 다시 NFC로 정규화한 키를 1~80자로 제한한다. casefold의 확장으로 80자를 넘는 이름도 거부한다.

호환 정규화(NFKC), 악센트/기호 제거, 동의어 병합은 하지 않는다. `한글`과 `한글`, `Straße`와 `STRASSE`는 같은 키를 사용한다. `C++`, `C#`, 전각 `Ｃ＋＋`는 서로 다른 태그다. 40개의 `ß`는 80자 키로 허용하고 40개의 `ﬃ`는 120자 키가 되어 거부한다.

같은 정규화 키는 계정·Board에 관계없이 같은 ID와 최초 표시명을 재사용한다. 먼저 commit된 삽입이 표시명을 결정하며 나중 요청으로 이름을 덮어쓰지 않는다. DB 고유 인덱스와 `INSERT ... ON CONFLICT DO NOTHING`을 사용해 동시 요청도 한 행으로 수렴한다. Tag 생성 시 현재 active User에 공유 잠금을 얻어 계정 비활성화·삭제와 직렬화한다.

## API

모든 경로는 `/api/v1` 기준이다.

| Method | Path | 입력·응답 |
| --- | --- | --- |
| GET | /tags | 공개 검색. `q` 기본 빈 문자열, `limit` 기본20·1~50. 200 `{ "items": [{ "id": "UUID", "name": "C++" }] }` |
| POST | /tags | 현재 active 계정의 Bearer 세션 전용. `{ "name": " C++ " }`. 신규201, 기존 키 재사용200에 동일한 `{ "id": "UUID", "name": "C++" }` |

검색어는 이름과 같은 정규화/문자 정책을 사용하되 빈 문자열을 허용한다. 정규화 전 Unicode 조합 문자의 길이가 길더라도 정규화 후 표시명이 40자 이하면 허용한다. 빈 검색어는 전체 사전의 앞부분을 반환한다. 키의 부분일치이며 `%`·`_`·escape 문자는 SQL wildcard가 아닌 문자 그대로 비교한다. 검색어를 SQL에 보간하지 않는다. 결과는 정규화 키의 binary 순서와 UUID 오름차순이다. PostgreSQL의 키 열은 `C` collation, SQLite는 기본 binary collation을 사용한다.

공개 사전의 존재 자체는 공개 정보다. 응답은 ID/표시명만 포함하고 정규화 키·계정/작성자·Canvas 연결·제한 콘텐츠의 사용 건수를 반환하지 않는다. 검색·생성 요청의 추가 필드, 명시적 null, 잘못된 이름/한도는 422다. POST는 API Key로 대체할 수 없고 성공 시 `Cache-Control: private, no-store`를 반환한다. 세션 없음은401, 비활성/삭제 계정은 기존 `USER_NOT_FOUND`404, DB 실패는 `TAG_UNAVAILABLE`503이다.

독립 Tag 상세 경로는 제공하지 않으므로 POST에 `Location` 헤더를 넣지 않는다. 이전 전체 API 설계의 사용자별 생성/검색 분당30회는 제안이었으며 현재 구현에는 적용하지 않는다. 익명 공개 검색을 포함한 분산 rate limit은 후속이다. 이번 API는 입력·검색 결과 수를 제한하며 처리량 SLA를 보장하지 않는다. 부분일치 검색은 사전 전체를 scan할 수 있고 결과 limit가 scan 비용을 제한하지는 않는다. 사전이 커지면 실제 비용을 측정하고 검색 인덱스/별도 검색 전략을 검토한다.

## Canvas 메타데이터

`CanvasCreateForm.tag_ids`는 UUID 배열이며 생략 시 빈 배열이다. metadata PATCH에서는 `expected_revision`과 함께 전달하고 생략 시 기존 연결을 유지하며 빈 배열이면 모두 해제한다. 최대10개이고 중복 UUID, 잘못된 UUID, null/없는 Tag는 거부한다. `name`을 Canvas 입력에 직접 넣어 자동 생성하지 않는다. 사전 POST 결과 ID를 사용한다.

```json
{
  "expected_revision": 0,
  "title": "태그가 있는 캔버스",
  "tag_ids": ["00000000-0000-4000-8000-000000000001"]
}
```

생성/조회/PATCH/복구의 `canvas.tags`는 검색과 같은 순서의 ID/표시명 요약 배열이다. 작성자 전용 Canvas 응답을 공개 사전 응답과 섞지 않는다. 공식 User Interest 최대8·Board Interest 최대3의 사전·API는 그대로이며 Board 생성/수정에서 `tag_ids`를 허용하지 않는다.

기존 `CanvasAccessService`가 현재 계정·작성자·active 멤버·Board 상태와 원본/대상 Shelf 읽기·작성 정책을 검사한다. Owner/Admin/Moderator와 앱 전역 관리자도 타인의 초안을 수정할 수 없다. 등급 강등·제재·정책 변경 뒤 새 쓰기를 오래된 권한으로 우회하지 못한다. 휴지통 편집은409, 보관 Board 쓰기는403, 타인/없는 Canvas나 접근 불가능한 멤버·Board는 기존404 경계를 따른다.

현재 권한과 기대 metadata revision을 검사한 뒤 같은 트랜잭션에서 제목/요약/분류/공개 범위·태그 연결을 변경한다. 실제 변경이 있으면 metadata revision과 updated_at을 한 번 갱신한다. 같은 태그 집합은 입력 순서가 달라도 no-op이다. no-op도 stale revision이면409이며 본문 revision/본문/Asset refs/outbox는 변경하지 않는다. 없는 Tag는422 `CANVAS_INVALID_TAGS`, 알려지지 않은 DB 실패는503 `CANVAS_UNAVAILABLE`이며 부분 변경·부분 생성은 rollback한다. OpenAPI의 생성/PATCH 422에는 도메인 오류와 입력 검증 배열을 모두 선언한다.

## 저장소와 마이그레이션

`routers/v1/tag.py → services/tag.py → models/tag.py`에서 요청을 처리한다. SQL·세션·트랜잭션·ORM 쓰기·DB 오류 변환은 모델이 소유한다. Canvas 모델은 같은 세션의 `TagTransaction`을 조합하고 서비스는 DTO/현재 정책만 조정한다. `tag_ids`는 ORM 열이 아니므로 metadata 입력 필드 목록과 실제 ORM 열 목록을 분리한다. 별도 Repository 파일을 만들지 않는다.

태그 변경 잠금은 기존 **Board → 활성 User 공유 잠금 → Canvas → UUID 순서의 Tag 공유 잠금**을 따른다. 기존 metadata revision 검사는 Board/Canvas 잠금 안에서 수행하며 SQLite 쓰기는 `BEGIN IMMEDIATE`로 직렬화한다. 본문 PUT은 기존 문서 전용 CAS·Asset 잠금/정리 루프를 그대로 사용한다.

`0028_canvas_tags`는 다음 두 테이블과 인덱스만 추가한다. 기존 Canvas/Document/Asset/ref/outbox 테이블을 재생성하거나 데이터를 복사하지 않는다.

- `tags`: UUID PK, 표시명40/정규화 키80, 비어 있지 않은 길이 CHECK와 정규화 키 고유 인덱스.
- `canvas_tags`: `(canvas_id, tag_id)` 복합 PK, Canvas 삭제 CASCADE, Tag 삭제 RESTRICT, tag_id 조회 인덱스.

계정 삭제는 Canvas.author_id를 SET NULL로 바꾸고 연결과 사전은 보존한다. Canvas/Board 삭제는 연결을 지우되 다른 Canvas와 전역 Tag를 지우지 않는다. 태그 이름 변경·삭제 API는 제공하지 않는다. downgrade는 두 새 테이블만 제거하므로 태그/연결 데이터는 제거되며 기존 콘텐츠는 보존한다.

## 검증과 후속

정규화/HTTP 계약·실제 API Key 거부와 SQLite 통합으로 공개 검색 최소 응답, 두 Board 재사용, 생성/PATCH 검증, 단일 revision/no-op·stale, 권한·rollback, 본문/Asset refs 보존과 FK/삭제 동작을 검사한다. 실제 로컬 PostgreSQL 고유 schema에서 이전0027의 데이터를 만든 뒤0028로 올려 보존을 확인하고 중복 생성·metadata CAS 경쟁, 권한 회수의 실제 lock wait, 실패 rollback·FK를 검증한다. 임시 schema를 제거하며 기존 DB 데이터·파일에는 접근하지 않는다. 실행 결과와 루트 전체 검증은 [worklog0293](../../worklog/0293-canvas-tags.md)에 기록한다.

UI/추천·사용 건수·전체 발견·Board 자유 Tag·Tag 수정/삭제·분산 rate limit은 후속이다. [#51 게시 snapshot](canvas-publication.md)은 제목과 태그 ID/표시명/순서를 publication revision에 고정한다. 공개 단건 응답과 후속 공개 태그 필터는 mutable canvas_tags가 아닌 canvas_publication_tags를 사용한다. 초안 태그 변경은 재게시 전 공개본에 반영하지 않는다.
