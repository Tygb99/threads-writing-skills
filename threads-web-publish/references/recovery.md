# 발행 검증과 복구

게시 결과가 불분명하거나 발행 후 수정·답글 교체·고정이 필요할 때 읽는다.
Aside 앱과 대상 계정의 로그인이 필요하다. `aside guide`를 읽고 `aside exec`으로 위임한다.
직접 확인은 `aside guide repl`을 읽은 뒤 REPL로 한다. [실행 양식](aside-setup.md)을 따른다.
대상 permalink·정본 파일·허용된 변경을 확인하고 행동 직전 `TZ=Asia/Seoul date`를 기록한다.
작업 중 새로고침하지 않는다. 팝업은 X로 닫고 작성 취소 확인창은 `취소`로 돌아간다.
화면의 상태와 내 행동의 인과를 구분하며, 모르는 결과는 미확인으로 남긴다.

## 작성창이 사라졌을 때

1. 다음 입력·재게시를 멈춘다. 사용자가 “게시된 것 같다”고 말하면 먼저 그 가능성을 확인한다.
2. 프로필 피드 최상단에서 본문 첫 줄·시각·첨부·답글을 확인한다. 같은 첫 줄의 글이 있으면 다시 게시하지 않는다.
3. 글이 없으면 새 글 작성창의 `임시 저장본`에서 예약·초안을 확인한다.
4. 업로드 실패 토스트의 `보기`가 있으면 복원된 작성창에서 정본과 본문·자답글·미디어·alt를 대조한다.
5. 텍스트 검색 한 번의 실패를 미게시로 판단하지 않는다. 새 snapshot과 스크린샷으로 렌더링 상태를 확인한다.
6. 확인되지 않으면 미확인으로 보고하며 결과가 확인될 때까지 중복 실행하지 않는다.

게시 버튼은 현재 작성 dialog 안의 `게시`로 찾는다.
확장 답글 작성창이 `role="menu"`이면 그 작성 menu 안에서 찾는다.
버튼 클릭 뒤 작성창 소멸은 전환 신호이며, 실제 글·예약본 확인이 완료 판정이다.

## 이름 없는 버튼의 정체 확인

`(no name)`은 이름이 없다는 뜻이다. 주변 설명이나 위치만으로 기능을 단정하지 않는다.
`게시`·`삭제`·`저장 안 함`과 연결될 수 있는 버튼은 새 snapshot의 ref에서 텍스트·aria-label·범위·좌표를 확인한다.
다음 `targetButton1`은 현재 snapshot에서 관찰한 후보 locator다.

```javascript
console.log(await targetButton1.evaluate(el => {
  const rect = el.getBoundingClientRect();
  return {
    text: el.textContent,
    aria: el.getAttribute('aria-label'),
    scope: el.closest('[role="dialog"], [role="menu"]')?.getAttribute('role'),
    rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
  };
}));
```

스크린샷과 DOM으로 기능이 확인됐을 때만 누른다. 위치를 클릭해야 하면 뷰포트와 스크린샷 배율을 먼저 맞춘다.

## 발행 후 15분 안의 수정

본문 오류는 15분 안에 게시물 `··· → 수정 → 완료`로 고친다.
`수정`은 **게시물 메뉴 `div[role="menu"]` 내부**에서 찾는다. 사이드바의 “피드 수정”을 누르지 않는다.

1. 대상 permalink와 게시 시각을 확인해 요청한 글의 메뉴를 연다.
2. 수정창의 본문 칸을 클릭하고 `activeElement`가 그 칸인지 확인한다.
3. 전체 교체는 `cmd+A → Delete`로 비운다. REPL의 macOS 키 표기는 `Meta+A`다. DOM Range 삭제만으로 수정창을 비우지 않는다.
4. 비어 있는지 확인하고 정본을 `keyboard.type`으로 다시 입력한다. 여러 줄은 `execCommand('insertText')`로 넣지 않는다.
5. 한글·공백·빈 줄까지 문자 대조하고 `완료`를 누른 뒤 실제 게시물에서 반영을 확인한다.

한 곳만 치환할 때는 선택 영역 delete 후 insertText 순서를 지키고 결과를 대조한다.
두 곳 이상이면 전체를 다시 입력한다.
수정 가능 시간이 지났거나 메뉴가 없으면 자동 삭제·재게시하지 말고 가능한 조치와 미확인 사유를 보고한다.
**alt는 발행 후 수정할 수 없으므로 본문 수정 창으로 복구할 수 없다.**

### 링크 카드가 수정창에 보일 때

발행 전에 제거한 링크 카드가 수정창의 미리보기로 나타날 수 있다.
수정창에는 카드만 제거하는 X가 없으므로 미리보기 때문에 문안을 바꾸지 않는다.
실제 발행 페이지와 API의 첨부 필드로 상태를 확인한다.
게시 전 초안에서 원치 않는 카드는 마지막 저장 직전에 X로 제거하며, 임시 저장본을 다시 열면 재생성될 수 있다.

## 답글에 이미지 추가

이미 발행한 답글의 수정창에서는 이미지를 추가할 수 없다.
이미지 포함 새 답글이 필요한 요청은 다음 순서로 처리한다.

1. 기존 답글의 텍스트·위치·고정 여부를 확인하고 이미지와 alt를 준비한다.
2. 확장 답글 작성창에서 새 답글을 입력·문자 대조한다. 인라인 Enter는 즉시 게시이므로 사용하지 않는다.
3. 세션 tmp의 이미지를 `input[type=file]`에 `setInputFiles`로 첨부하고 `··· → 대체 텍스트 추가 → 완료`로 저장한다. `img.alt`를 정본과 대조한다.
4. 새 답글을 먼저 게시하고 텍스트·이미지·alt·대상 부모 글을 화면에서 확인한다.
5. 요청된 교체 범위에 따라 기존 답글을 삭제하고, 필요하면 새 답글을 고정한다.

삭제가 요청 범위에 없다면 새 답글과 기존 답글의 상태를 보고한다.
답글 수정 취소의 “수정 사항을 삭제하시겠어요?”는 편집 내용 취소이며 원 답글 삭제와 다르다. 확인창 문구를 읽고 대상 동작을 구분한다.

## 답글 고정 교체

1. 요청한 답글의 `··· → 답글 고정`을 누른다.
2. 기존 고정이 있으면 “현재 고정된 메시지를 바꾸시겠어요?” 확인창의 `확인`을 누른다.
3. 새 snapshot과 화면에서 새 답글의 `고정됨` 배지를 확인한다. 메뉴가 닫힌 것만으로 완료라고 보고하지 않는다.

## 공식 API 확정 검증

**발행 직후는 화면 확인, 발행 시각 +16분 이후는 API 확정 대조**다.
15분 수정 창 안의 변경은 차이만 기록한다. 그 차이만으로 오류나 조작 주체를 단정하지 않는다.
요청 대상의 계정·shortcode·permalink·시각을 맞춘 뒤 각 글의 확정값을 기록한다.

토큰은 `THREADS_ACCESS_TOKEN` 환경변수에서만 읽는다.
명령 추적을 켜거나 토큰을 출력·문서·결과 보고에 넣지 않는다.
조회는 [Meta 공식 Threads API 컬렉션](https://www.postman.com/meta/threads/documentation/dht3nzz/threads-api)의 게시물 조회·대화 조회 형식을 따른다.

```sh
curl --fail --silent --show-error --get \
  --header "Authorization: Bearer ${THREADS_ACCESS_TOKEN:?토큰 환경변수 필요}" \
  --data-urlencode 'fields=id,shortcode,permalink,timestamp,media_type,text,is_quote_post' \
  'https://graph.threads.net/v1.0/me/threads'
```

목록의 첫 항목이라고 대상 글로 가정하지 않는다. 필요한 경우 응답의 페이지를 더 읽어 실제 ID를 확인한다.
확인한 ID를 `THREADS_MEDIA_ID`에 넣고 개별 게시물과 캐러셀 항목을 확인한다.

```sh
curl --fail --silent --show-error --get \
  --header "Authorization: Bearer ${THREADS_ACCESS_TOKEN:?토큰 환경변수 필요}" \
  --data-urlencode 'fields=id,permalink,text,timestamp,media_type,media_url,alt_text,link_attachment_url,children{id,media_type,media_url,alt_text}' \
  "https://graph.threads.net/v1.0/${THREADS_MEDIA_ID:?확인한 게시물 ID 필요}"
```

- `text`를 칸별 정본과 문자 단위로 대조한다. 자답글은 각 게시물 ID에 대해 확인한다.
- `media_type`·`media_url`·캐러셀 `children`으로 사진·영상·첨부 순서를 확인한다. 링크는 `link_attachment_url`도 확인한다.
- `alt_text`는 개별 첨부별로 정본과 비교한다. 필드가 없거나 권한 오류가 나면 미확인으로 둔다.
- 댓글의 의미는 아래 `conversation`을 끝까지 읽고 시각순으로 확인한다. 일부 요약으로 판단하지 않는다.

```sh
curl --fail --silent --show-error --get \
  --header "Authorization: Bearer ${THREADS_ACCESS_TOKEN:?토큰 환경변수 필요}" \
  --data-urlencode 'fields=id,text,timestamp,username,permalink,media_type,media_url,alt_text' \
  "https://graph.threads.net/v1.0/${THREADS_MEDIA_ID:?확인한 게시물 ID 필요}/conversation"
```

토큰·권한·실행 수단이 없거나 +16분이 지나지 않았으면 확정 검증을 완료라고 쓰지 않는다.
permalink, 즉시 화면 확인 결과, 칸별 문자 대조, 첨부·alt 결과, 실제 게시 KST 시각과 +16분 확인 예정·완료 시각을 보고한다.
24h·72h 성과 크론은 없으며 별도 성과 타이머를 등록하지 않는다.
