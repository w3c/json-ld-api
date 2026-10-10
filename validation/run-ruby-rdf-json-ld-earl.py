#!/usr/bin/env python3
"""Generate a Ruby RDF JSON-LD EARL report for this test suite."""

import os
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
            "usage: run-ruby-rdf-json-ld-earl.py IMPLEMENTATION_DIR TESTS_DIR OUTPUT_FILE"
        )

    implementation_dir = directory(sys.argv[1])
    tests_dir = directory(sys.argv[2])
    output_file = Path(sys.argv[3]).resolve()
    suite_parent = implementation_dir / "spec" / "json-ld-api"
    suite_link = suite_parent / "tests"
    if suite_link.exists() or suite_link.is_symlink():
        raise ValueError(f"Expected a fresh implementation clone; {suite_link} already exists")

    suite_parent.mkdir(parents=True, exist_ok=True)
    suite_link.symlink_to(tests_dir)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    sh.Command("bundle")(
        "exec",
        "ruby",
        str(Path(__file__).with_name("ruby-rdf-json-ld-earl.rb")),
        "--earl",
        "--output",
        str(output_file),
        _cwd=str(implementation_dir),
        _env={
            **os.environ,
            "RUBY_RDF_JSON_LD_DIR": str(implementation_dir),
        },
        _out=sys.stdout,
        _err=sys.stderr,
    )


if __name__ == "__main__":
    main()
