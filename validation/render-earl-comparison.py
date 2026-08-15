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
        f"## {report.implementation.name} conformance",
        "",
        f"Implementation commit: `{report.implementation.commit}`",
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
            "usage: render-earl-comparison.py COMPARISONS_DIR POPULATED.json SUMMARY.md"
        )

    comparisons_directory, populated_path, summary_path = map(Path, sys.argv[1:])
    report = read_comparison(
        comparisons_directory,
        populated_path,
        os.environ["IMPLEMENTATION_NAME"],
        os.environ["IMPLEMENTATION_COMMIT"],
    )

    with summary_path.open("a", encoding="utf-8") as summary:
        summary.write(render_markdown(report))

    if report.has_regressions:
        print(
            f"::error title={report.implementation.name} regression::"
            "See the job summary for affected tests."
        )
    return int(report.has_regressions)


if __name__ == "__main__":
    raise SystemExit(main())
