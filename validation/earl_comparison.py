"""Typed EARL comparison data built from SPARQL JSON results."""

from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, BaseModel


class ChangeCategory(str, Enum):
    REGRESSED = "Regressed"
    IMPROVED = "Improved"
    NEW_ASSERTION = "New assertion"
    NO_LONGER_ASSERTED = "No longer asserted"


class Outcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    UNTESTED = "untested"
    NOT_ASSERTED = "Not asserted"


class SparqlTerm(BaseModel):
    value: str


class SparqlBinding(BaseModel):
    category: SparqlTerm
    test: SparqlTerm
    baselineOutcome: SparqlTerm
    candidateOutcome: SparqlTerm


class SparqlResults(BaseModel):
    bindings: list[SparqlBinding]


class SparqlSelectResponse(BaseModel):
    results: SparqlResults


class SparqlComparisonResponses(BaseModel):
    responses: list[SparqlSelectResponse]


class SparqlAskResponse(BaseModel):
    boolean: bool


class AffectedTest(BaseModel):
    category: ChangeCategory
    test: AnyHttpUrl
    published_outcome: Outcome
    candidate_outcome: Outcome

    @property
    def label(self) -> str:
        parsed = urlparse(str(self.test))
        return f"{Path(parsed.path).name}#{parsed.fragment}"


class Implementation(BaseModel):
    name: str
    commit: str


class ComparisonReport(BaseModel):
    implementation: Implementation
    affected_tests: list[AffectedTest]

    @property
    def has_regressions(self) -> bool:
        return any(
            change.category is ChangeCategory.REGRESSED
            for change in self.affected_tests
        )

    @property
    def regressions(self) -> list[AffectedTest]:
        return [
            change
            for change in self.affected_tests
            if change.category is ChangeCategory.REGRESSED
        ]

    @property
    def summary(self) -> "ComparisonSummary":
        summary = ComparisonSummary(implementation=self.implementation)
        for change in self.affected_tests:
            if change.category is ChangeCategory.REGRESSED:
                summary.regressed += 1
            elif change.category is ChangeCategory.IMPROVED:
                summary.improved += 1
            elif change.category is ChangeCategory.NEW_ASSERTION:
                if change.candidate_outcome is Outcome.PASSED:
                    summary.new_passed += 1
                else:
                    summary.new_failed += 1
            elif change.category is ChangeCategory.NO_LONGER_ASSERTED:
                summary.no_longer_asserted += 1
        return summary


class ComparisonSummary(BaseModel):
    implementation: Implementation
    available: bool = True
    regressed: int = 0
    improved: int = 0
    new_passed: int = 0
    new_failed: int = 0
    no_longer_asserted: int = 0


CATEGORY_ORDER = {category: index for index, category in enumerate(ChangeCategory)}


def read_comparison(
    comparisons_directory: Path,
    populated_path: Path,
    implementation_name: str,
    implementation_commit: str,
) -> ComparisonReport:
    populated = SparqlAskResponse.model_validate_json(
        populated_path.read_text(encoding="utf-8")
    )
    if not populated.boolean:
        raise ValueError("The published or candidate EARL report has no assertions")

    response_paths = sorted(comparisons_directory.glob("*.json"))
    if not response_paths:
        raise ValueError(f"No comparison responses in {comparisons_directory}")
    comparisons = SparqlComparisonResponses(
        responses=[
            SparqlSelectResponse.model_validate_json(path.read_text(encoding="utf-8"))
            for path in response_paths
        ]
    )
    affected_tests = [
        AffectedTest(
            category=binding.category.value,
            test=binding.test.value,
            published_outcome=binding.baselineOutcome.value,
            candidate_outcome=binding.candidateOutcome.value,
        )
        for response in comparisons.responses
        for binding in response.results.bindings
    ]
    affected_tests.sort(
        key=lambda change: (CATEGORY_ORDER[change.category], str(change.test))
    )
    return ComparisonReport(
        implementation=Implementation(
            name=implementation_name,
            commit=implementation_commit,
        ),
        affected_tests=affected_tests,
    )
