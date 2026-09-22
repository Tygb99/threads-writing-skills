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
    if explicit:
        return explicit
    for cand in CHROME_CANDIDATES:
        if Path(cand).exists():
            return cand
        found = shutil.which(cand)
        if found:
            return found
    sys.exit("Chrome/Chromium을 찾지 못했다. --chrome 으로 경로를 지정할 것")


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        sys.exit(f"PNG가 아니다: {path}")
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Threads 브랜드 카드 HTML을 headless Chrome으로 PNG로 렌더한다"
    )
    ap.add_argument("html")
    ap.add_argument("png")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1350)
    ap.add_argument("--chrome")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    html = Path(args.html).resolve()
    if not html.exists():
        sys.exit(f"HTML이 없다: {html}")
    png = Path(args.png).resolve()
    png.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            find_chrome(args.chrome),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-dev-shm-usage",
            "--force-device-scale-factor=1",
            f"--user-data-dir={profile}",
            f"--window-size={args.width},{args.height}",
            f"--screenshot={png}",
            html.as_uri(),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            if not png.exists() or png.stat().st_size == 0:
                sys.exit(f"렌더가 {args.timeout}초 안에 끝나지 않았다: {png}")

    if not png.exists() or png.stat().st_size == 0:
        sys.exit(f"렌더 실패: {png}")

    got = png_size(png)
    if got != (args.width, args.height):
        sys.exit(f"크기 불일치: 기대 {args.width}x{args.height}, 실제 {got[0]}x{got[1]}")

    print(f"rendered={png}")
    print(f"size={got[0]}x{got[1]}")
    print(f"bytes={png.stat().st_size}")


if __name__ == "__main__":
    main()
