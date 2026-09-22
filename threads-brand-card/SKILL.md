---
name: threads-brand-card
description: "Threads(스레드)용 브랜드 카드 이미지를 HTML과 PNG로 만든다. '카드 만들어줘', '요약 이미지', '인포그래픽', '브랜드 넣어줘', '내 브랜드로', '워터마크 넣어줘' 요청에 사용한다. 브랜드 값 입력, 테마 선택, 사진 비율에 맞춘 크기, 렌더와 대체 텍스트를 다룬다."
---

# Threads 브랜드 카드

## 언제 쓰는가

Threads에 올릴 글자·숫자 중심 카드를 계정 브랜드로 만들 때 사용한다.
브랜드 바를 고정하고 카드 내용을 교체한다. 한글과 숫자의 재현성을 위해 이미지 생성 모델을 쓰지 않고 HTML/CSS를 headless Chrome으로 렌더한다.
순수 사진 편집이나 다른 채널 이미지는 대상이 아니다.

## 브랜드 값 입력

이 스킬 폴더의 `brand.local.example.md`를 같은 폴더의 `brand.local.md`로 복사한다.
`brand.local.md`는 사용자 제공 입력이며 Git 추적 대상에서 제외된다. 견본의 가짜 값을 실제 브랜드로 쓰지 않는다.
파일이 없으면 표시 이름, 한 줄 소개, 핸들, 링크, 마크 PNG의 절대 경로를 사용자에게 물어 작성한다. 값을 추측하지 않는다.

UTF-8 파일에 아래 표와 언어 표시 없는 코드블록을 넣는다. 항목 이름과 백틱을 그대로 유지한다.
값 안의 세로줄은 `\|`로 쓰며, 백틱이나 줄바꿈은 넣지 않는다.

| 항목 | 값 |
|---|---|
| 표시 이름 | `예시 브랜드` |
| 한 줄 소개 | `기록하는 사람` |
| 핸들 | `@sample.note` |
| 링크 | `example.com` |

마크 경로는 실제 존재하는 `.png` 파일의 절대 경로 한 줄이다. `~`나 따옴표를 쓰지 않는다.

```
/absolute/path/to/brand-mark.png
```

`scripts/fill_brand.py`는 이 형식을 읽어 `BRAND_*`를 채운다. 누락 항목, 없는 마크, 남은 토큰은 실패 처리한다.
기본 입력은 이 스킬 폴더의 `brand.local.md`와 `assets/themes/theme-06-forest-press.html`이다.
다른 파일은 `--brand`, `--template`으로 지정한다. 지정 파일만 읽고 마크 파일의 존재를 확인하며, 폴더를 재귀 탐색하지 않는다.
옵션·출력·종료 코드는 각 스크립트의 `--help`가 정본이다. Python 3.9+ 표준 라이브러리만 필요하며 렌더에는 Chrome 또는 Chromium도 필요하다.

## 마크·색·크기 규격

### 마크

- 계정 프로필 이미지를 정사각으로 크롭한 PNG를 쓴다. 얼굴이나 로고가 중앙에 오게 한다.
- 마크는 카드 크기와 무관하게 `74px` 정사각, `border-radius: 50%`, `object-fit: cover`, 강조색 `3px` 테두리다.
- 템플릿의 `BRAND_MARK_ABSOLUTE_PATH.png`는 채우기 스크립트가 치환한다. 마크 자체에는 `alt=""`를 둔다.
- 실제 마크와 개인 브랜드가 채워진 산출물은 사용자 작업 폴더에 둔다.

### 색

기본 카드 템플릿 `assets/brand-card-template.html`의 팔레트다. 테마를 선택하면 해당 테마의 팔레트를 유지한다.

```text
배경    #0f1115
패널    #171b22
본문    #e9edf4
보조    #97a0b1
링크    #5b6478
강조    #6ee7a8
경고    #f2708a
구분선  #232a35
```

강조색은 한 카드에서 3곳 이내로 쓴다.

### 크기

| 상황 | 크기 |
|---|---|
| 카드 한 장 | `1080x1350` |
| 실사진과 함께 | 사진 비율에 맞춤. 세로 3:4이면 `1080x1440` |
| 정사각 카드뉴스 | `1080x1080` |

사진 비율은 EXIF 방향을 반영한 픽셀 크기로 판단한다. 회전 전 폭·높이만 읽지 않는다.
Pillow가 있는 사진 작업 환경에서는 `ImageOps.exif_transpose(Image.open(photo_path)).size`로 확인한다.
사진을 내보낼 때도 같은 함수로 회전을 픽셀에 반영한다. 비율이 다른 사진은 늘이지 말고 공통 비율로 패딩한다.
HTML `body`의 고정 px 폭·높이와 렌더 명령의 크기를 일치시킨다. 테마 원본은 `1080x1440`이므로 단독 카드에는 작업용 HTML의 높이를 조정한다.

## 테마

기본 테마는 `theme-06-forest-press`다. 파일은 모두 `assets/themes/` 안에 있다.

| 파일 | 이름 | 배경·특징 |
|---|---|---|
| `theme-01-warm-paper.html` | 크림 페이퍼 | 아이보리, 따뜻한 색 |
| `theme-02-neon-gradient.html` | 네온 그라디언트 | 보라·남색, 숫자 그라디언트 |
| `theme-03-mono-white.html` | 신문 라이트 | 순백, 구분선, 빨간 밑줄 |
| `theme-04-blueprint.html` | 설계도 | 진청 격자, 점선 패널 |
| `theme-05-forest.html` | 숲 | 딥그린, 라임 숫자 배지 |
| `theme-06-forest-press.html` | 숲 신문 | 딥그린, 신문 레이아웃 |
| `theme-07-mono-dark.html` | 신문 다크 | `#121212`, 빨간 강조 |

테마의 예시 글은 이번 게시물 내용으로 교체한다. 테마를 바꿔도 마크 규격은 유지한다.

## 절차

아래 `<plugin-root>`는 설치한 저장소의 절대 경로, `<work>`는 사용자 작업 폴더로 바꾼다.

1. 브랜드 값을 확인하고 HTML을 채운다.

   ```bash
   python3 "<plugin-root>/skills/threads-brand-card/scripts/fill_brand.py" "<work>/card.html" \
     --brand "<work>/brand.local.md" \
     --template "<plugin-root>/skills/threads-brand-card/assets/themes/theme-06-forest-press.html"
   ```

2. 작업용 HTML의 주제 라벨, 헤드라인, `.rows`, 결론을 이번 글 내용으로 교체한다. 브랜드 바의 구조와 스타일은 유지한다.
3. 함께 올리는 사진의 EXIF 방향과 비율을 확인하고 `body` 크기를 결정한다.
4. 같은 크기로 렌더한다. 아래는 카드 한 장의 예다.

   ```bash
   python3 "<plugin-root>/skills/threads-brand-card/scripts/render_brand_card.py" \
     "<work>/card.html" "<work>/card.png" --width 1080 --height 1350
   ```

5. PNG를 열어 한글 잘림, 패널 겹침, 빈 마크, 대비, 하단 브랜드 바 눌림을 눈으로 확인한다. 문제가 있으면 HTML을 고쳐 다시 렌더한다.
6. 이미지 안 글자를 그대로 옮겨 alt를 작성한다. 형식은 `alt-text-generator`의 `<plugin-root>/skills/alt-text-generator/SKILL.md`를 따른다.

렌더 세부 규칙과 점검표는 `threads-html-image`의 `<plugin-root>/skills/threads-html-image/SKILL.md`를 따른다.
첨부는 `threads-web-publish`의 `<plugin-root>/skills/threads-web-publish/SKILL.md`를 따른다.
스크립트 회귀 검증은 `python3 -m unittest discover -s "<plugin-root>/skills/threads-brand-card/scripts" -p 'test_*.py'`로 실행한다.

## 내용 규칙

- 헤드라인 하나와 핵심 숫자 하나가 먼저 읽히게 한다. 숫자는 2~3개까지 쓴다.
- 본문이 말하지 않는 수치를 카드에 담는다. 본문을 그대로 반복해 alt와 중복시키지 않는다.
- 한국어는 `letter-spacing: 0`을 쓴다. CSS와 시스템 한국어 폰트 스택은 HTML 안에 둔다.
- 화살표는 `->`를 쓴다. 이모지와 `vw`·`vh` 단위는 쓰지 않는다.
- 크기가 맞아도 렌더된 내용이 비거나 잘리면 완료로 보지 않는다.

## 브랜드 바를 빼는 경우

- 남의 화면을 그대로 보여주는 스크린샷에는 붙이지 않는다.
- 원글 정보가 이미 표시되는 인용카드 이미지에는 붙이지 않는다.
- 보조 설명 카드에는 마크와 핸들만 남기고 소개 문구를 뺀다.
