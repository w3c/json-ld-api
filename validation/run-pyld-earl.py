#!/usr/bin/env python3
"""Generate a PyLD EARL report for this test suite."""

import sys
from pathlib import Path

import sh


def directory(path: str) -> Path:
    resolved = Path(path).resolve()
    if not resolved.is_dir():
        raise ValueError(f"Expected a directory: {resolved}")
    return resolved


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "usage: run-pyld-earl.py IMPLEMENTATION_DIR TESTS_DIR OUTPUT_FILE"
        )

    implementation_dir = directory(sys.argv[1])
    tests_dir = directory(sys.argv[2])
    output_file = Path(sys.argv[3]).resolve()
    runner = implementation_dir / "tests" / "runtests.py"
    if not runner.is_file():
        raise ValueError(f"Expected the PyLD test runner: {runner}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    sh.Command(sys.executable)(
        str(runner),
        "--earl",
        str(output_file),
        str(tests_dir),
        _cwd=str(implementation_dir),
        _out=sys.stdout,
        _err=sys.stderr,
        _ok_code=[0, 1],
    )
    if not output_file.is_file() or output_file.stat().st_size == 0:
        raise ValueError(f"PyLD did not create an EARL report: {output_file}")


if __name__ == "__main__":
    main()
