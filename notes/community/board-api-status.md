# Board API 구현 범위

2026-11-03, main `32fbcd1`의 라우터·서비스·[OpenAPI](../../contracts/openapi.json)와 이슈 #22/#23/#25를 대조한 상태다. [설계 진입점](README.md)

| 범위 | 현재 상태·계약 |
| --- | --- |
| 개설·목록·검색·상세·slug 조회 | 구현. Owner/기본 등급·정책/Shelf/홈/Interest를 한 트랜잭션으로 생성한다. |
| 기본 정보·규칙·Interest·공개/가입 정책 | PATCH 구현. Board 공개/정책·현재 역할을 검사한다. |
| 공개 가입·탈퇴 | POST join / DELETE membership 구현. 현재 기본 등급·마지막 Owner 보호를 적용한다. |
| 회원 목록·운영 역할·제재·수동 승강·감사 | 구현. 역할과 활동 등급을 분리한다. 역할별 운영 권한표 자체를 임의 편집하는 기능은 제공하지 않는다. |
| Board별 등급 정의 | 목록/추가/이름·기본값 수정/순서/삭제·대체 구현. |
| 수동 초대 | 기존 계정을 active Member로 등록하는 POST members 구현. 이메일/토큰 초대는 후속이다. |
| 소유권 위임·보관/복원·영구 삭제 | 구현. 보관 Board 확인 삭제와 에셋 정리 outbox를 연결한다. |
| Shelf·액션 정책 | CRUD/전체 순서·숨김·직접 조회·Board 기본/Shelf 재정의 정책 구현. |
| 기본 홈 조회 | GET home 구현. 공식 자유 배치 편집/동적 공개 게시글 위젯 완료를 뜻하지 않는다. |

따라서 기본 커뮤니티 운영 API는 마련됐지만 Board 관련 전체 계획의 완료 상태는 아니다. 대표 이미지/커버의 실제 미디어 연결(#22), 공식 홈 레이아웃 PUT과 위젯 데이터(#25), Shelf/Board의 공개 Canvas 목록과 게시/Plaza(#8)는 남아 있다. 가입 승인·이메일/토큰 초대 고도화·활동량 자동 승급도 후속이다. 제품 UI는 보류한다.

기존 설계의 `GET /boards/{id}/membership` 전용 경로는 현재 라우터/OpenAPI에 없다. 본인 membership/capabilities는 현재 Board 상세/홈 응답에 포함된다. 별도 조회 경로의 필요성·최종 계약은 #22에서 추적하며 모든 목표 endpoint가 구현됐다고 표시하지 않는다.

이번 객체 스키마 작업은 Board 라우터·서비스·DB 저장 동작을 변경하지 않는다. 최신 게시/병합 상태와 개별 수용 기준은 [#22](https://github.com/Blueprint4Agent/Canvanity/issues/22), [#23](https://github.com/Blueprint4Agent/Canvanity/issues/23), [#25](https://github.com/Blueprint4Agent/Canvanity/issues/25)를 따른다.
