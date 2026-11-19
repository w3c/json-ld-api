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


class ComparisonReport(BaseModel):
    implementation_commit: str
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


CATEGORY_ORDER = {category: index for index, category in enumerate(ChangeCategory)}


def read_comparison(
    comparison_path: Path,
    populated_path: Path,
    implementation_commit: str,
) -> ComparisonReport:
    populated = SparqlAskResponse.model_validate_json(
        populated_path.read_text(encoding="utf-8")
    )
    if not populated.boolean:
        raise ValueError("The published or candidate EARL report has no assertions")

    response = SparqlSelectResponse.model_validate_json(
        comparison_path.read_text(encoding="utf-8")
    )
    affected_tests = [
        AffectedTest(
            category=binding.category.value,
            test=binding.test.value,
            published_outcome=binding.baselineOutcome.value,
            candidate_outcome=binding.candidateOutcome.value,
        )
        for binding in response.results.bindings
    ]
    affected_tests.sort(
        key=lambda change: (CATEGORY_ORDER[change.category], str(change.test))
    )
    return ComparisonReport(
        implementation_commit=implementation_commit,
        affected_tests=affected_tests,
    )
