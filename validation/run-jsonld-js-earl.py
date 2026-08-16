#!/usr/bin/env python3
"""Generate a jsonld.js EARL report for this test suite."""

import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import sh


class QuietRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def directory(path: str) -> Path:
    resolved = Path(path).resolve()
    if not resolved.is_dir():
        raise ValueError(f"Expected a directory: {resolved}")
    return resolved


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "usage: run-jsonld-js-earl.py IMPLEMENTATION_DIR TESTS_DIR OUTPUT_FILE"
        )

    implementation_dir = directory(sys.argv[1])
    tests_dir = directory(sys.argv[2])
    manifest = tests_dir / "manifest.jsonld"
    if not manifest.is_file():
        raise ValueError(f"Expected the JSON-LD API manifest: {manifest}")
    output_file = Path(sys.argv[3]).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    handler = partial(QuietRequestHandler, directory=str(tests_dir))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    port = server.server_address[1]
    try:
        sh.Command("npm")(
            "test",
            _cwd=str(implementation_dir),
            _env={
                **os.environ,
                "TESTS": f"http://127.0.0.1:{port}/manifest.jsonld",
                "EARL": str(output_file),
            },
            _out=sys.stdout,
            _err=sys.stderr,
            _ok_code=[0, 1],
        )
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()

    if not output_file.is_file() or output_file.stat().st_size == 0:
        raise ValueError(f"jsonld.js did not create an EARL report: {output_file}")


if __name__ == "__main__":
    main()
