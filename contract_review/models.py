"""Core data contracts that flow between pipeline stages.

These dataclasses are the spine of the workflow: each stage is a function from
one contract to the next (segment -> match -> assess -> verify -> report).
Kept stdlib-only on purpose so the data shapes stay framework-independent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Verdict(str, Enum):
    """Three-way disposition of a contract toward a playbook rule.

    Mirrors ContractNLI's label set exactly so the evaluation oracle can compare
    predicted verdicts to gold annotations without translation.
    """

    ENTAILMENT = "Entailment"
    CONTRADICTION = "Contradiction"
    NOT_MENTIONED = "NotMentioned"


@dataclass(frozen=True)
class Span:
    """A contiguous clause-sized unit of a document (a sentence or list item)."""

    id: str  # stable identifier, e.g. "s42"
    start: int  # character offset into Document.text, inclusive
    end: int  # character offset into Document.text, exclusive
    text: str

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < self.start:
            raise ValueError(f"invalid span offsets: [{self.start}, {self.end})")


@dataclass
class Document:
    """A contract: full text plus its segmentation into spans."""

    id: str
    source_name: str
    text: str
    spans: list[Span] = field(default_factory=list)

    def span_by_id(self, span_id: str) -> Span | None:
        for span in self.spans:
            if span.id == span_id:
                return span
        return None


@dataclass(frozen=True)
class Rule:
    """One playbook requirement.

    `statement` is the hypothesis tested against the contract. `expected_disposition`
    is the reviewer's desired verdict; a deviation is any actual verdict that
    differs from it. The expected disposition is what turns a topic-checker into a
    review tool — without it we can report what a contract says but not whether
    that is a problem.
    """

    id: str
    name: str
    statement: str
    expected_disposition: Verdict


@dataclass(frozen=True)
class Playbook:
    """A named, ordered set of rules.

    A swappable artifact, deliberately decoupled from any dataset: the v1 content
    happens to be ContractNLI's 17 hypotheses, but a user can supply their own.
    """

    id: str
    name: str
    rules: tuple[Rule, ...]

    def __len__(self) -> int:
        return len(self.rules)

    def rule_by_id(self, rule_id: str) -> Rule | None:
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None


@dataclass
class RetrievedContext:
    """Output of the match stage: where in *this* document a rule is relevant.

    An abstraction over the retrieve-vs-long-context decision. Downstream stages
    only see candidate spans plus the text block to reason over — never how that
    context was gathered — so the retrieval strategy can change without touching
    the assess stage.
    """

    rule_id: str
    candidate_span_ids: list[str]
    context_text: str


@dataclass
class Assessment:
    """Output of the (agentic) assess stage: a grounded verdict for one rule."""

    rule_id: str
    verdict: Verdict
    evidence_span_ids: list[str]
    rationale: str


@dataclass
class VerifiedAssessment:
    """An assessment after the verify/reflect loop has accepted or repaired it."""

    assessment: Assessment
    checks_passed: bool
    attempts: int
    notes: str = ""


@dataclass
class Finding:
    """A single per-rule result in the final report."""

    rule_id: str
    rule_name: str
    expected: Verdict
    actual: Verdict
    is_deviation: bool
    evidence_span_ids: list[str]
    rationale: str
    suggested_redline: str | None = None


@dataclass
class Report:
    """The deliverable handed to a human for sign-off."""

    document_id: str
    playbook_id: str
    findings: list[Finding]
    deviation_score: float  # fraction of rules that deviate, in [0, 1]
    summary: str = ""

    @property
    def deviations(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.is_deviation]
