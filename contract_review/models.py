"""Core data contracts that flow between pipeline stages.

These Pydantic v2 models are the spine of the workflow: each stage is a function
from one contract to the next (segment -> match -> assess -> verify -> report).
Pydantic gives validation at boundaries, JSON (de)serialization for the API,
persistence, and evals, and schema generation we reuse for the assess tool.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Verdict(str, Enum):
    """Three-way disposition of a contract toward a playbook rule.

    Mirrors ContractNLI's label set exactly so the evaluation oracle can compare
    predicted verdicts to gold annotations without translation.
    """

    ENTAILMENT = "Entailment"
    CONTRADICTION = "Contradiction"
    NOT_MENTIONED = "NotMentioned"


class Span(BaseModel):
    """A contiguous clause-sized unit of a document (a sentence or list item)."""

    model_config = ConfigDict(frozen=True)

    id: str  # stable identifier, e.g. "s42"
    start: int = Field(ge=0)  # character offset into Document.text, inclusive
    end: int  # character offset into Document.text, exclusive
    text: str

    @model_validator(mode="after")
    def _check_offsets(self) -> Span:
        if self.end < self.start:
            raise ValueError(f"invalid span offsets: [{self.start}, {self.end})")
        return self


class Document(BaseModel):
    """A contract: full text plus its segmentation into spans."""

    id: str
    source_name: str
    text: str
    spans: list[Span] = Field(default_factory=list)

    def span_by_id(self, span_id: str) -> Span | None:
        for span in self.spans:
            if span.id == span_id:
                return span
        return None


class Rule(BaseModel):
    """One playbook requirement (a rubric criterion).

    `statement` is the hypothesis tested against the contract. `expected_disposition`
    is the reviewer's desired verdict; a deviation is any actual verdict that
    differs from it. The expected disposition is what turns a topic-checker into a
    review tool.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    statement: str
    expected_disposition: Verdict


class Playbook(BaseModel):
    """A named, ordered set of rules (a rubric).

    A swappable artifact, deliberately decoupled from any dataset.
    """

    model_config = ConfigDict(frozen=True)

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


class RetrievedContext(BaseModel):
    """Output of the match stage: where in *this* document a rule is relevant.

    An abstraction over the retrieve-vs-long-context decision. Downstream stages
    only see candidate spans plus the text block to reason over.
    """

    rule_id: str
    candidate_span_ids: list[str]
    context_text: str


class Assessment(BaseModel):
    """Output of the (agentic) assess stage: a grounded verdict for one rule."""

    rule_id: str
    verdict: Verdict
    evidence_span_ids: list[str] = Field(default_factory=list)
    rationale: str = ""


class VerifiedAssessment(BaseModel):
    """An assessment after the verify/reflect loop has accepted or repaired it."""

    assessment: Assessment
    checks_passed: bool
    attempts: int
    notes: str = ""


class Finding(BaseModel):
    """A single per-rule result in the final report."""

    rule_id: str
    rule_name: str
    expected: Verdict
    actual: Verdict
    is_deviation: bool
    evidence_span_ids: list[str] = Field(default_factory=list)
    rationale: str = ""
    suggested_redline: str | None = None


class Report(BaseModel):
    """The deliverable handed to a human for sign-off."""

    document_id: str
    playbook_id: str
    findings: list[Finding] = Field(default_factory=list)
    deviation_score: float  # fraction of rules that deviate, in [0, 1]
    summary: str = ""

    @property
    def deviations(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.is_deviation]
