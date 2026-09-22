import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="정본과 실제 텍스트 파일을 Unicode 문자 단위로 대조한다.",
        epilog=(
            "Python 3.9+ 표준 라이브러리만 사용한다. 입력은 UTF-8 파일 2개이며 "
            "인자로 받은 파일만 읽는다. 상대 경로 기준은 현재 작업 디렉터리다. "
            "디렉터리 탐색·재귀·패턴 확장·정렬은 하지 않는다. "
            "기본값은 완전 일치 비교이며 줄바꿈 형식과 Unicode 조합도 보존한다. "
            "출력: 양쪽 길이, 첫 차이의 0부터 시작하는 문자 인덱스와 "
            "정본 기준 1부터 시작하는 행·열, 서로 다른 문자 또는 EOF. "
            "종료 코드: 0 일치 또는 --help, 1 불일치, 2 인자·파일·UTF-8 오류."
        ),
    )
    parser.add_argument("expected", type=Path, help="정본 UTF-8 텍스트 파일")
    parser.add_argument("actual", type=Path, help="작성창 또는 API에서 읽은 UTF-8 텍스트 파일")
    parser.add_argument(
        "--rstrip-actual",
        action="store_true",
        help="실제 값에만 rstrip()을 적용해 끝 공백·탭·개행을 제거한다. 정본은 보존한다.",
    )
    args = parser.parse_args()
    try:
        expected = args.expected.read_bytes().decode("utf-8")
        actual = args.actual.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as error:
        print(f"입력 오류: {error}", file=sys.stderr)
        return 2

    if args.rstrip_actual:
        actual = actual.rstrip()
    print(f"길이: 정본 {len(expected)}, 실제 {len(actual)} (Unicode 문자, 개행 포함)")
    if expected == actual:
        print("일치: 첫 차이: 없음")
        return 0

    index = next(
        (i for i, (left, right) in enumerate(zip(expected, actual)) if left != right),
        min(len(expected), len(actual)),
    )
    line = expected.count("\n", 0, index) + 1
    column = index - expected.rfind("\n", 0, index)
    left = repr(expected[index]) if index < len(expected) else "EOF"
    right = repr(actual[index]) if index < len(actual) else "EOF"
    print(f"불일치: 첫 차이 인덱스 {index} (0부터), 정본 {line}행 {column}열 (1부터)")
    print(f"정본 {left} / 실제 {right}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
