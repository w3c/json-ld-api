#!/usr/bin/env python3
"""Render a compact PR comment from implementation comparison summaries."""

import os
import sys
from pathlib import Path

from earl_comparison import ComparisonSummary


def report_cell(summary: ComparisonSummary) -> str:
    return "✅ Available" if summary.available else "❌ Unavailable"


def count_cell(summary: ComparisonSummary, field: str) -> str:
    return str(getattr(summary, field)) if summary.available else ""


def markdown_row(summary: ComparisonSummary) -> str:
    return "| {} | `{}` | {} | {} | {} | {} | {} | {} |".format(
        summary.implementation.name,
        summary.implementation.commit,
        report_cell(summary),
        count_cell(summary, "regressed"),
        count_cell(summary, "improved"),
        count_cell(summary, "new_passed"),
        count_cell(summary, "new_failed"),
        count_cell(summary, "no_longer_asserted"),
    )


def render_markdown(summaries: list[ComparisonSummary], workflow_url: str) -> str:
    lines = [
        "# JSON-LD implementation conformance",
        "",
        f"[Open the full test-by-test report in this workflow run]({workflow_url}).",
        "",
        "| Implementation | Commit | Report | Regressed | Improved | New passed | New failed | No longer asserted |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        *(markdown_row(summary) for summary in summaries),
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(
            "usage: render-conformance-comment.py COMMENT.md SUMMARY.json [SUMMARY.json ...]"
        )

    comment_path = Path(sys.argv[1])
    summary_paths = map(Path, sys.argv[2:])
    summaries = [
        ComparisonSummary.model_validate_json(path.read_text(encoding="utf-8"))
        for path in summary_paths
    ]
    comment_path.write_text(
        render_markdown(summaries, os.environ["WORKFLOW_URL"]), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
