---
name: threads-html-image
description: "Threads(스레드) 이미지를 HTML/CSS로 만들고 headless Chrome으로 PNG로 렌더한다. 'html로 이미지', '이미지html', 'HTML 카드', 'PNG로 뽑아줘', '카드뉴스', '타임라인 이미지', '표를 이미지로', '스크린샷 합쳐줘', '렌더해줘' 요청에 사용한다. HTML 규칙, 사진 비율, 렌더 검증과 첨부를 다룬다."
---

# Threads HTML 이미지

## 언제 쓰는가

한국어 글자·숫자·표·타임라인이 들어간 Threads 이미지를 만들 때 사용한다.
이미지 생성 모델 대신 HTML/CSS와 headless Chrome을 써서 글자와 수치를 재현한다.
산출물은 HTML과 PNG다. 순수 사진 편집, 출처 화면을 그대로 보여주는 스크린샷, 다른 채널 이미지는 대상이 아니다.
브랜드 카드는 `threads-brand-card`의 `<plugin-root>/skills/threads-brand-card/SKILL.md`도 함께 따른다.

## 절차

1. 게시물 내용과 함께 첨부할 사진을 확인한다.
2. 아래 크기·HTML 규칙으로 작업용 HTML을 만든다.
3. 공용 렌더 스크립트로 PNG를 만들고 종료 코드와 `size=` 출력을 확인한다.
4. PNG를 열어 점검표를 확인한다. 문제가 있으면 HTML을 고쳐 다시 렌더한다.
5. 이미지 안 글자를 옮긴 alt를 준비하고 발행 스킬의 첨부 절차를 따른다.

### 공용 렌더 스크립트

이 저장소의 `threads-brand-card/scripts/render_brand_card.py`를 사용한다.
카드가 아닌 HTML 이미지에도 같은 스크립트를 쓴다.
아래 `<plugin-root>`는 설치한 저장소의 절대 경로, `<work>`는 사용자 작업 폴더로 바꾼다.

```bash
python3 "<plugin-root>/skills/threads-brand-card/scripts/render_brand_card.py" \
  "<work>/card.html" "<work>/card.png" --width 1080 --height 1350
```

Python 3.9+ 표준 라이브러리와 Chrome 또는 Chromium이 필요하다. 옵션·출력·종료 코드는 `--help`가 정본이다.
출력은 `rendered=<PNG 절대 경로>`, `size=<폭>x<높이>`, `bytes=<바이트 수>`다.
종료 코드는 성공·도움말 `0`, 파일·Chrome·렌더·크기 오류 `1`, 인자 오류 `2`다.

Chrome 탐색은 아래 순서로 실행 가능한 첫 후보를 선택한다. 폴더를 재귀 탐색하거나 패턴 검색·정렬하지 않는다.

1. `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
2. `/Applications/Chromium.app/Contents/MacOS/Chromium`
3. `PATH`의 `google-chrome`
4. `PATH`의 `chromium`

`PATH`는 등록된 디렉터리 순서로 확인한다. `--chrome "/absolute/path/to/chrome"`을 주면 그 실행 파일만 확인한다.
Chrome이 없으면 설치하거나 `--chrome`으로 실행 파일을 지정한다. 스크립트는 지정 HTML을 열며 Chrome은 HTML에 연결된 리소스를 읽는다.

`--timeout` 기본값은 60초다. 타임아웃이어도 이번 실행이 만든 PNG의 헤더와 크기가 정상이면 성공한다.
기존 PNG는 검증에 성공한 뒤 덮어쓴다. PNG 크기가 기대값과 다르면 결과물로 쓰지 않는다.
스크립트는 GPU를 끄지 않으며 `--no-first-run`, `--no-default-browser-check`, `--disable-dev-shm-usage`를 포함한다.
가속 경로에서 실패하면 원인을 확인하고 재시도한다. 하드웨어 가속이 지원되지 않거나 막힌 경우에만 CPU를 사용하고 이유를 알린다.

### 크기 규칙

| 상황 | 크기 |
|---|---|
| 이미지 한 장 | `1080x1350` |
| 실사진과 함께 | 사진 비율에 맞춤. 세로 3:4이면 `1080x1440` |
| 정사각 카드뉴스 | `1080x1080` |

사진 폭·높이는 EXIF 방향을 반영해서 잰다. `sips`의 회전 전 픽셀 크기만으로 비율을 정하지 않는다.
Pillow가 있는 사진 작업 환경에서는 `ImageOps.exif_transpose(Image.open(photo_path))`의 `.size`를 읽고 그 이미지로 내보낸다.
비율이 다른 사진은 공통 비율로 패딩한다. 같은 비율의 사진만 동일 픽셀 크기로 리사이즈하며 늘여 맞추지 않는다.
HTML의 `body` 폭·높이와 `--width`·`--height`를 함께 바꾼다. 렌더 옵션만 바꾸면 내용이 잘릴 수 있다.

### HTML 규칙

- CSS는 HTML 안에 넣는다. 외부 스타일시트와 네트워크 폰트를 쓰지 않는다.
- 폰트는 `-apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", sans-serif`를 쓴다.
- `body`의 폭·높이는 고정 px로 지정한다. `vw`·`vh`를 쓰지 않는다.
- 한국어는 `letter-spacing: 0`으로 둔다.
- 로컬 이미지는 절대 경로로 연결한다.
- 화살표는 `->`를 쓴다. 이모지를 넣지 않는다.

## 렌더 후 검증 점검표

PNG를 열어 직접 확인한다. 하나라도 실패하면 HTML을 수정하고 다시 렌더한다.

- [ ] 렌더가 종료 코드 `0`이고 `size=`가 요청한 크기다.
- [ ] 내용과 이미지가 비지 않았으며 샘플 문구나 자리표시자가 남지 않았다.
- [ ] 한국어의 마지막 줄, 긴 단어, 숫자가 잘리지 않았다.
- [ ] 패널이 겹치거나 하단 문구·브랜드 바를 누르지 않는다.
- [ ] 글자와 배경의 대비가 충분하다.
- [ ] 줄바꿈이 어색한 위치에서 일어나지 않는다.

크기 검사 통과만으로 완료하지 않는다. 눈으로 확인한 PNG가 결과물이다.

## 첨부 시 유의

- Aside가 읽을 수 있는 세션 임시 폴더로 파일을 복사하고 `input[type=file]`에 `setInputFiles`로 첨부한다. 외장 볼륨 원본 경로를 그대로 넘기지 않는다.
- webp는 첨부하지 않는다. 카드와 스크린샷은 PNG로 만든다.
- 카드 alt에는 이미지 안 글자를 그대로 옮긴다. 본문이 말하지 않는 수치를 카드에 담아 중복 낭독을 줄인다.
- 이미지의 `···` → `대체 텍스트 추가` → 입력 → `완료` 뒤 저장된 `img.alt`를 확인한다. alt는 발행 전에 넣는다.
- alt 형식은 `alt-text-generator`의 `<plugin-root>/skills/alt-text-generator/SKILL.md`를 따른다.
- 첨부·발행은 `threads-web-publish`의 `<plugin-root>/skills/threads-web-publish/SKILL.md`를 따른다.
