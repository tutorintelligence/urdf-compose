from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

HOME_PATH = Path(__file__).parent

"""
CI scripts
"""


def isort(check: bool = False) -> None:
    check_cmd = ["--check"] if check else []
    subprocess.run(["isort", "."] + check_cmd, check=True)


def black(check: bool = False) -> None:
    check_cmd = ["--check"] if check else []
    subprocess.run(["black", "."] + check_cmd, check=True)


def flake8() -> None:
    subprocess.run(["flake8"], check=True)


def mypy() -> None:
    subprocess.run(["mypy", "."], check=True)


def test() -> None:
    subprocess.run(["pytest"], check=True)


def style() -> None:
    parser = argparse.ArgumentParser(description="Style.")

    parser.add_argument(
        "--check",
        action="store_true",
        help="error if failing style",
    )

    args = parser.parse_args()

    isort(check=args.check)
    black(check=args.check)
    flake8()
    mypy()


def remove_unused() -> None:
    subprocess.run(
        ["autoflake", "--in-place", "--remove-all-unused-imports", "-r", "."],
        check=True,
    )
