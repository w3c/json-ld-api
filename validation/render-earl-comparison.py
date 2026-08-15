#!/usr/bin/env python3
"""Render a Markdown job summary from a typed EARL comparison report."""

import os
import sys
from pathlib import Path

from earl_comparison import AffectedTest, ComparisonReport, read_comparison


OUTCOME_ICONS = {
    "passed": "✅",
    "failed": "❌",
    "untested": "⚪",
    "Not asserted": "➖",
}


def outcome_cell(outcome: str) -> str:
    return f"{OUTCOME_ICONS[outcome]} {outcome}"


def markdown_row(change: AffectedTest) -> str:
    return (
        f"| {change.category.value} | [{change.label}]({change.test}) | "
        f"{outcome_cell(change.published_outcome.value)} | "
        f"{outcome_cell(change.candidate_outcome.value)} |"
    )


def render_markdown(report: ComparisonReport) -> str:
    lines = [
        "## Ruby RDF JSON-LD conformance",
        "",
        f"Implementation commit: `{report.implementation_commit}`",
        "",
    ]
    if report.affected_tests:
        lines.extend(
            [
                "| Change | Test | Published report | Candidate report |",
                "| --- | --- | --- | --- |",
                *(markdown_row(change) for change in report.affected_tests),
            ]
        )
    else:
        lines.append("No affected tests.")
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit(
            "usage: render-earl-comparison.py COMPARISON.json POPULATED.json SUMMARY.md"
        )

    comparison_path, populated_path, summary_path = map(Path, sys.argv[1:])
    report = read_comparison(
        comparison_path,
        populated_path,
        os.environ["IMPLEMENTATION_COMMIT"],
    )

    with summary_path.open("a", encoding="utf-8") as summary:
        summary.write(render_markdown(report))

    run_url = "/".join(
        [
            os.environ["GITHUB_SERVER_URL"],
            os.environ["GITHUB_REPOSITORY"],
            "actions/runs",
            os.environ["GITHUB_RUN_ID"],
        ]
    )
    print(
        "::notice title=EARL comparison report::"
        f"View the full report in the run Summary: {run_url}"
    )
    for regression in report.regressions:
        print(
            "::error title=Ruby RDF JSON-LD regression::"
            f"{regression.test} changed from passed to failed"
        )
    return int(report.has_regressions)


if __name__ == "__main__":
    raise SystemExit(main())
