#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
)


def find_chrome(explicit: str | None) -> str:
    for cand in (explicit,) if explicit else CHROME_CANDIDATES:
        found = shutil.which(cand)
        if found:
            return found
    sys.exit(
        "Chrome/Chromium 실행 파일을 찾지 못했다.\n"
        "Google Chrome(https://www.google.com/chrome/) 또는 Chromium을 설치한다.\n"
        '설치 위치가 다르면 --chrome "/absolute/path/to/chrome"으로 실행 파일을 지정한다.\n'
        "자동 탐색 후보와 순서는 --help에서 확인한다."
    )


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as fh:
        head = fh.read(24)
    if len(head) != 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        sys.exit(f"PNG가 아니다: {path}")
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Threads HTML을 headless Chrome으로 PNG로 렌더한다. Python 3.9+ 표준 라이브러리만 사용한다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Chrome 탐색 순서 (--chrome을 생략한 경우):
  1. /Applications/Google Chrome.app/Contents/MacOS/Google Chrome
  2. /Applications/Chromium.app/Contents/MacOS/Chromium
  3. PATH의 google-chrome
  4. PATH의 chromium
  앞에서부터 실행 가능한 첫 후보를 쓴다. PATH는 등록 순서대로 조회한다.
  다른 폴더를 재귀 탐색하거나 패턴 검색·정렬하지 않는다.
  --chrome을 지정하면 그 실행 파일 또는 PATH 명령만 확인한다.

렌더와 검증:
  지정 HTML과 그 안에서 참조하는 리소스를 Chrome이 읽는다.
  GPU를 강제로 끄지 않고 Chrome의 기본 가속 경로를 사용한다.
  --no-first-run --no-default-browser-check --disable-dev-shm-usage를 사용한다.
  --timeout은 Chrome 대기 시간이며 기본 60초다.
  타임아웃이어도 이번 실행이 생성한 PNG의 헤더·크기가 정상이면 성공한다.
  PNG 크기가 --width/--height와 다르면 실패한다. HTML의 body 크기도 맞춰야 한다.
  검증한 PNG만 출력 경로에 저장하며 기존 PNG는 성공할 때 덮어쓴다.
  출력 부모 폴더를 만들고 임시 Chrome 프로필은 종료 시 제거한다.

출력: stdout에 rendered=<절대 PNG 경로>, size=<폭>x<높이>, bytes=<바이트 수>.
종료 코드: 0 성공/도움말, 1 파일·Chrome·렌더·PNG 크기 오류, 2 CLI 인자 오류.
""",
    )
    ap.add_argument("html", help="입력 HTML 경로")
    ap.add_argument("png", help="출력 PNG 경로")
    ap.add_argument("--width", type=int, default=1080, help="PNG 폭, 양의 정수 픽셀 (기본: 1080)")
    ap.add_argument("--height", type=int, default=1350, help="PNG 높이, 양의 정수 픽셀 (기본: 1350)")
    ap.add_argument("--chrome", help="Chrome 실행 파일 경로 또는 PATH 명령 (생략 시 아래 순서로 탐색)")
    ap.add_argument("--timeout", type=int, default=60, help="Chrome 대기 제한, 양의 정수 초 (기본: 60)")
    args = ap.parse_args()
    if min(args.width, args.height, args.timeout) <= 0:
        ap.error("--width, --height, --timeout은 양의 정수여야 한다")

    html = Path(args.html).resolve()
    if not html.is_file():
        sys.exit(f"HTML이 없다: {html}")
    chrome = find_chrome(args.chrome)
    png = Path(args.png).resolve()
    png.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".threads-render-", dir=png.parent) as profile:
        rendered = Path(profile) / "card.png"
        cmd = [
            chrome,
            "--headless=new",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-dev-shm-usage",
            "--force-device-scale-factor=1",
            f"--user-data-dir={profile}",
            f"--window-size={args.width},{args.height}",
            f"--screenshot={rendered}",
            html.as_uri(),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            if not rendered.exists() or rendered.stat().st_size == 0:
                sys.exit(f"렌더가 {args.timeout}초 안에 끝나지 않았다: {png}")
        except subprocess.CalledProcessError as error:
            sys.exit(f"Chrome 렌더 실패 (종료 코드 {error.returncode}): {error.stderr.decode(errors='replace').strip()}")

        if not rendered.exists() or rendered.stat().st_size == 0:
            sys.exit(f"렌더 실패: {png}")

        got = png_size(rendered)
        if got != (args.width, args.height):
            sys.exit(f"크기 불일치: 기대 {args.width}x{args.height}, 실제 {got[0]}x{got[1]}")
        rendered.replace(png)

    print(f"rendered={png}")
    print(f"size={got[0]}x{got[1]}")
    print(f"bytes={png.stat().st_size}")


if __name__ == "__main__":
    try:
        main()
    except OSError as error:
        sys.exit(f"파일 또는 Chrome 실행 실패: {error}")
