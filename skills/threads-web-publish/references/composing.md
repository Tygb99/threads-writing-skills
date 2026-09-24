# 작성창 입력과 첨부

본문·자답글·사진·영상·alt·텍스트 첨부를 준비할 때 읽는다.
Aside 앱과 Threads 로그인이 필요하다. `aside guide`를 읽고 `aside exec`으로 위임한다.
직접 조작할 때만 `aside guide repl`을 읽고 REPL을 사용한다. [실행 양식](aside-setup.md)을 따른다.
입력은 칸별 정본 UTF-8 파일과 첨부·alt 절대경로다. 작업 중 새로고침하지 않는다.
팝업은 X로 닫고, 작성 취소 확인창에서는 `취소`를 누른다. `저장 안 함`은 복구할 수 없다.

## 작성창과 입력칸

새 글 모달은 자체가 편집창이다. 확장 버튼은 인라인 답글에만 있다.
**인라인 답글창의 Enter는 즉시 게시**이므로 여러 줄은 확장창에서 쓴다.
인라인을 써야 하면 한 줄씩 입력하고 줄 경계에서 `Shift+Enter`를 누른다.
확장 작성창은 `role="menu"`로 나타날 수 있다. 새 글의 `role="dialog"`와 구분한다.

새 snapshot에서 작성창과 입력칸의 ref를 찾고 클릭한다.
다음 예의 `composer1`은 확인한 작성창 locator다. 반환된 active 인덱스가 목표 칸과 같을 때만 입력한다.

```javascript
console.log(await composer1.evaluate(root => {
  const editors = [...root.querySelectorAll('[contenteditable="true"]')];
  return {
    count: editors.length,
    active: editors.indexOf(root.ownerDocument.activeElement),
    placeholders: editors.map(el => el.getAttribute('aria-placeholder'))
  };
}));
```

alt 패널과 텍스트 첨부 편집기도 `contenteditable`이다. 칸 번호를 외우지 말고 매번 용도·포커스를 확인한다.
일반 본문·자답글 칸 수를 셀 때는 이 별도 편집기들을 제외한다.

## 입력과 치환

- 여러 줄 정본은 `page.keyboard.type(text)`으로 통째로 넣는다. 한글은 리터럴이나 UTF-8 파일 그대로 전달한다.
- `document.execCommand('insertText', false, text)`는 `\n`을 무시한다. 한 줄 입력이나 한 곳 치환에만 사용한다.
- 한 곳 치환은 기존 문구를 선택해 `delete`한 뒤 `insertText`한다. 옛 문구가 없어지고 새 문구가 한 번만 남았는지 대조한다.
- 두 곳 이상 바꾸거나 링크 경계가 포함되면 해당 칸에 포커스를 두고 `Meta+A → Delete`로 비운 뒤 전체를 다시 타이핑한다. DOM의 내용을 직접 교체하지 않는다.
- 클릭만으로 캐럿이 끝에 간다고 가정하지 않는다. 현재 입력칸의 Range를 `selectNodeContents`한 뒤 `collapse(false)`로 끝에 놓을 수 있다.
- 본문 끝 개행은 서버가 제거한다. 카드 옆에서 지우다가 첨부까지 지울 수 있으므로 그대로 두고 대조 시 실제 값만 `rstrip()`한다. 중간 공백·빈 줄은 보존한다.

### 멘션과 주제 태그

`@`로 시작하는 낱말은 패키지명 같은 문자열도 멘션으로 링크될 수 있다.
자동완성 팝업이 떠 있는 동안 Enter는 후보 선택이다.

1. 팝업이 생긴 위치에서 입력을 멈춘다.
2. 실제로 의도한 계정 후보를 클릭해 확정한다. 후보가 맞지 않으면 선택하지 말고 커서를 옮겨 팝업을 정리한다.
3. 확정 뒤 붙은 꼬리 공백을 제거한다. Backspace가 듣지 않으면 마지막 텍스트 노드의 공백만 Range로 선택해 Delete한다.
4. 팝업이 닫힌 것을 확인한 뒤 줄바꿈하고 나머지를 입력한다.

해시태그는 기본 0개다. Threads는 글당 주제 태그 1개 모델이므로 여러 태그를 본문에 나열하지 않는다.
사용자가 태그를 지정한 경우에도 자동완성 처리 후 정본과 문자 단위로 대조한다.

## 문자 단위 대조

정본은 게시할 텍스트만 담으며 불필요한 파일 끝 개행 없이 준비한다.
정본의 길이와 끝 개행은 `python3 -c "t=open('body.txt',encoding='utf-8').read();print(len(t), repr(t[-3:]))"`로 확인한다.
작성창 값을 읽을 때 `innerText`의 공백·개행을 임의로 치환하지 않는다.
아래 `bodyEditor1`은 새 snapshot으로 확인한 본문 입력칸 locator다.

```javascript
const actualBody1 = await bodyEditor1.innerText();
await fs.mkdir('./artifacts', { recursive: true });
await fs.writeFile('./artifacts/body-actual.txt', actualBody1);
console.log(actualBody1);
```

세션 결과 파일을 호출 측 셸로 가져와 아래 예의 경로를 실제 절대경로로 바꿔 실행한다.

```sh
python3 <스킬 절대경로>/scripts/compare_text.py --help
python3 <스킬 절대경로>/scripts/compare_text.py --rstrip-actual <본문 정본.txt> <작성창 본문.txt>
python3 <스킬 절대경로>/scripts/compare_text.py <alt 정본.txt> <DOM에서 읽은 alt.txt>
```

도구는 Python 3.9+ 표준 라이브러리만 쓰고 인자로 받은 두 UTF-8 파일만 읽는다.
상대 경로의 시작점은 현재 작업 디렉터리다. 디렉터리 탐색·재귀·포함/제외 패턴·정렬은 없다.
기본값은 완전 일치 비교다. `--rstrip-actual`은 실제 값 끝의 공백·탭·개행만 제거하며 정본에는 적용하지 않는다.
행 구분(CRLF/LF)과 Unicode 조합도 자동으로 바꾸지 않는다. 위치는 문자 인덱스 0부터, 정본 행·열 1부터다.
출력은 양쪽 길이와 첫 차이 위치·문자이며, 일치하면 첫 차이가 없다고 표시한다.
종료 코드는 0=일치 또는 도움말, 1=불일치, 2=인자·파일·UTF-8 오류다.
글자 수가 같아도 내용이 다르면 실패한다. 본문·자답글·alt·장문 카드마다 대조하고, 실패한 칸을 고친 뒤 전 칸을 확인한다.

## 자답글 체인

1. 본문을 채운 뒤 `스레드에 추가`를 눌러 다음 칸을 만든다. 따로 게시하면 의도한 체인 순서가 달라질 수 있다.
2. 칸이 늘면 추가 버튼이 뷰포트 밖으로 밀린다. 새 ref를 사용하고, 필요하면 작성창 안에서 스크롤한 뒤 스크린샷으로 버튼이 창 안쪽에 있는지 확인한다.
3. 클릭 뒤 본문 `contenteditable` 개수가 실제로 늘었는지 확인한다. 늘지 않았다면 이전 좌표로 다시 클릭하지 않는다.
4. 입력 전 `activeElement` 인덱스와 새 칸을 대조한다. 각 칸을 입력·대조한 뒤 한 번에 게시한다.

## 사진 준비와 첨부

- WebP는 받지 않으므로 PNG로 변환한다.
- 실사는 JPEG를 유지하고 긴 변 2000px 이내, 품질 85~90으로 준비한다. 실사를 PNG로 바꿔 용량을 키우지 않는다.
- 스크린샷과 글자·선 그래픽은 PNG로 준비한다.
- EXIF 방향은 `ImageOps.exif_transpose`로 픽셀에 반영한 후 방향 태그가 다시 적용되지 않게 저장한다. 이 전처리는 설치된 이미지 도구에서 수행하며 문자 대조 스크립트의 의존성이 아니다.
- 단독 1장은 원본 비율이다. 2장 이상은 같은 4:5 캔버스에 패딩해 핵심 내용의 잘림을 막는다.
- 업로드 실패 시 프로필에서 실제 발행 여부를 확인한 뒤 파일 용량부터 줄인다. 실패 토스트의 `보기`로 초안을 복원할 수 있으면 본문·자답글·첨부·alt를 먼저 확인한다.

호출 측 셸에서 원본 파일을 현재 Aside 세션 tmp에 복사한다.
현재 작성창 안의 `input[type=file]`을 확인하고 `locator.setInputFiles`로 첨부한다.
여러 칸에 파일 input이 있으면 칸별 범위를 좁힌다. 파일 목록 순서를 정본의 첨부 순서와 맞춘다.
썸네일, 이미지 수, `naturalWidth`·`naturalHeight`, 방향을 확인한다.
첨부 직후 snapshot의 본문 textbox 라벨에 본문이 두 번 붙은 것처럼 보여도 접근성 이름 합성일 뿐이다. `innerText`로 다시 읽어 판단하고 다시 입력하지 않는다.
예약본을 다시 열면 이미지 주소가 `blob:`에서 CDN 주소로 바뀔 수 있다. 주소 접두사만으로 첨부를 세지 않는다.
실제 형식·방향·크기 확인을 마친 뒤 alt를 넣는다.

## 영상 첨부

MP4도 세션 tmp로 복사한 뒤 해당 `input[type=file]`에 `setInputFiles`로 넣는다.
썸네일만 보고 준비 완료라고 판단하지 않는다. 확인한 작성창의 `video` locator에서 아래 값을 읽는다.

```javascript
console.log(await video1.evaluate(el => ({
  readyState: el.readyState,
  width: el.videoWidth,
  height: el.videoHeight,
  duration: el.duration
})));
```

`readyState === 4`, 너비·높이, 재생시간이 원본과 맞을 때까지 `sleep(ms)`로 제한 시간을 정해 폴링한다.
시간 안에 준비되지 않으면 게시를 멈추고 미확인으로 보고한다. 영상에도 alt를 넣는다.
인코딩이 필요하면 GPU·하드웨어 가속부터 시도한다. macOS는 VideoToolbox의 `h264_videotoolbox`·`hevc_videotoolbox` 또는 도구의 하드웨어 옵션을 확인한다.
실패 원인을 해결하고 재시도하며, 지원되지 않거나 막힌 경우에만 이유를 밝히고 CPU를 쓴다.

## alt 저장과 재확인

1. 첨부 하단이 보이도록 스크롤한 뒤 hover하고 첨부 위의 `첨부 파일 옵션` 버튼(`img[aria-label="첨부 파일 옵션"]`, 화면에는 `···`)을 누른다. 메뉴는 `스포일러로 표시 / 사람 태그하기 / 대체 텍스트 추가` 순이며 `대체 텍스트 추가`를 고른다.
2. alt 대화상자는 새 글 dialog를 대체하는 같은 `role="dialog"`(제목 `대체 텍스트 추가`)로 뜬다. 이때 `contenteditable`은 본문 칸을 포함해 2개가 잡히고 alt 칸은 인덱스 1이다. 새 snapshot으로 alt 입력칸을 찾아 클릭하고 `activeElement`의 `aria-placeholder`가 `시각적으로`로 시작하는지 확인한다.
3. 해당 첨부의 alt 정본을 입력·문자 대조하고 `완료`를 누른다.
4. 저장 여부는 라벨로 판단하지 않는다. 메뉴는 저장 후에도 `대체 텍스트 추가`로 표시된다.
5. 작성창 첨부의 `img.alt`를 직접 읽어 정본과 비교한다. 영상은 `video`의 `aria-label`을 읽는다. DOM 값이 불명확할 때만 새 ref로 입력창을 다시 열어 확인한다.
6. 모든 첨부에 반복한다. 발행 후 alt를 수정할 수 없으므로 발행 전에 마친다.

예약 초안에서 alt만 바꿔 `업데이트`가 비활성이면 다음 순서로 저장한다.

1. alt를 완료한 뒤 본문 끝에 임시 문자 한 개를 추가하고 `업데이트`한다.
2. 같은 예약본을 다시 열어 임시 문자만 제거하고 `업데이트`한다.
3. 다시 열어 본문·alt·KST 예약 시각을 대조한다. 링크 카드가 재생성됐다면 마지막 저장 직전에 다시 제거한다.

## 텍스트 첨부: 장문 카드

본문과 별개의 장문 첨부이며 한도는 10,000자다. 개행 하나를 2자로 센다.
계산은 `len(text.replace('\n', '')) + 2 * text.count('\n')`이며 줄바꿈은 LF로 준비한다.
한도를 넘기면 입력이 잘리는 대신 `완료`가 비활성이 된다. `textContent.length`만으로 개행 포함 길이를 판단하지 않는다.

1. `svg[aria-label="텍스트 첨부"]`를 가진 버튼을 누른다. 도구줄 아이콘에 `aria-label`이 없으면 `svg > title` 텍스트(`텍스트 첨부`)로 찾는다.
2. `[contenteditable="true"][aria-placeholder="내용을 더 추가해보세요..."]` 편집기를 확인한다.
3. 정본을 여러 줄 `type`으로 입력하고, 줄·빈 줄을 포함한 전문을 문자 대조한 뒤 `완료`를 누른다.

사진·GIF·설문·음악과 상호 배타이며 예약할 수 없다.
`취소 → 임시 저장하시겠어요? → 저장`으로 준비해 둘 수 있고, 다시 열면 본문과 장문 카드가 유지된다.
발행 시각에 같은 초안을 열어 재대조하고 `게시`한다. 초안 저장을 예약 완료라고 보고하지 않는다.
초안 삭제는 항목의 `··· → 임시 저장본 삭제`이며 확인창 없이 실행되므로 첫 줄로 대상을 먼저 확인한다.

인용카드와 함께 쓰려면 **인용카드를 먼저 만들고 텍스트 첨부를 추가**한다.
첨부가 먼저 있으면 share URL을 넣어도 인용카드가 생기지 않는다.
임시 저장에서는 장문 카드만 남고 인용카드는 사라진다.
이 조합의 재개는 첨부 정본을 확보한 뒤 `첨부 삭제 → share URL로 인용카드 생성 → 텍스트 첨부 재입력` 순서로 한다.

## 입력 완료 점검

전 칸 문자 대조, 자답글 순서, 첨부 수·방향·비율·준비 완료, alt DOM 저장값을 확인한다.
파일명처럼 생긴 `CLAUDE.md`도 링크·카드를 만들 수 있으므로 URL 없는 칸도 확인한다.
원치 않는 링크 카드는 마지막 저장 직전에 제거한다.
게시 버튼은 현재 작성 dialog에 한정하고, 확장 답글이 menu이면 그 작성 menu에 한정한다.
누른 뒤 작성창 소멸과 실제 프로필 글을 확인하며, 예약은 [예약 절차](scheduling.md)를 따른다.
발행 직후 화면 확인과 +16분 [API 확정 검증](recovery.md#공식-api-확정-검증)을 구분한다.
