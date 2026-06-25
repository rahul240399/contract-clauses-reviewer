"""Prompts and tool schemas for the assess and redline stages.

Kept in one place so they can be tuned (the main lever on output quality) without
touching stage logic.
"""

from __future__ import annotations

from .models import Finding, RetrievedContext, Rule, Verdict

ASSESS_TOOL_NAME = "submit_assessment"

ASSESS_TOOL: dict = {
    "name": ASSESS_TOOL_NAME,
    "description": "Submit the verdict for one rule, grounded in the contract's clauses.",
    "parameters": {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": [v.value for v in Verdict],
                "description": "Entailment, Contradiction, or NotMentioned.",
            },
            "evidence_span_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Clause ids (e.g. 's12') that justify the verdict; empty for NotMentioned.",
            },
            "rationale": {
                "type": "string",
                "description": "One or two sentences justifying the verdict.",
            },
        },
        "required": ["verdict", "evidence_span_ids", "rationale"],
    },
}

ASSESS_SYSTEM = """\
You are a contract analyst performing document-level natural language inference.
You are given one RULE (a hypothesis about the contract) and the contract's
CLAUSES, each tagged with an id like [s12]. Decide the contract's disposition
toward the rule:

- Entailment: the contract supports or implies that the rule holds.
- Contradiction: the contract affirmatively states the opposite of the rule.
- NotMentioned: the contract is silent on the rule (neither supports nor opposes).

Key distinctions:
- NotMentioned means the contract does not address the point at all.
- Contradiction means the contract explicitly says the opposite.
- Watch for negation-by-exception: e.g. "all obligations end at termination,
  except confidentiality, which survives" ENTAILS a survival-of-obligations rule.

Ground every Entailment or Contradiction in the specific clause id(s) that
justify it, citing ids exactly as shown (e.g. s12). For NotMentioned, cite none.
"""


def _render_rule_and_clauses(rule: Rule, context: RetrievedContext) -> str:
    return (
        f"RULE [{rule.id}] {rule.name}:\n{rule.statement}\n\n"
        f"CLAUSES:\n{context.context_text}"
    )


def build_think_prompt(rule: Rule, context: RetrievedContext) -> str:
    return (
        _render_rule_and_clauses(rule, context)
        + "\n\nReason step by step: which clauses (if any) bear on this rule, and "
        "what is the correct verdict? Consider negation-by-exception. Do not give "
        "a final answer yet."
    )


def build_extract_prompt(rule: Rule, context: RetrievedContext, reasoning: str) -> str:
    return (
        _render_rule_and_clauses(rule, context)
        + f"\n\nYour reasoning so far:\n{reasoning}\n\n"
        f"Now call {ASSESS_TOOL_NAME} with the final verdict, the evidence clause "
        "ids drawn from the CLAUSES above, and a brief rationale."
    )


# --- Redline drafting (report stage) -----------------------------------------

REDLINE_TOOL_NAME = "submit_redline"

REDLINE_TOOL: dict = {
    "name": REDLINE_TOOL_NAME,
    "description": "Submit a proposed redline that brings a clause into line with the playbook.",
    "parameters": {
        "type": "object",
        "properties": {
            "redline": {
                "type": "string",
                "description": (
                    "The proposed amendment: revised or new clause language, "
                    "concise and ready to drop into the contract."
                ),
            },
        },
        "required": ["redline"],
    },
}

REDLINE_SYSTEM = """\
You are a contract attorney revising a contract on behalf of the party whose
playbook you are given. A clause's disposition deviates from the position the
playbook requires. Draft a concise, specific redline that brings the contract
into line with the expected position:

- If existing clause language is shown, propose a revised version of it.
- If the contract is silent on the point, propose new clause language to add.

Write only the proposed contract language (and a short lead-in like "Add:" or
"Replace with:" if helpful). No commentary, no explanation of your reasoning.
"""


def build_redline_prompt(rule: Rule, finding: Finding, clauses_text: str) -> str:
    existing = clauses_text.strip() or "(the contract is silent on this point)"
    rationale = finding.rationale.strip()
    rationale_line = f"Reviewer note: {rationale}\n" if rationale else ""
    return (
        f"RULE [{rule.id}] {rule.name}:\n{rule.statement}\n\n"
        f"Required position: {finding.expected.value}\n"
        f"Current contract disposition: {finding.actual.value}\n"
        f"{rationale_line}\n"
        f"Relevant existing clause text:\n{existing}\n\n"
        f"Call {REDLINE_TOOL_NAME} with a redline that achieves the required "
        f"position."
    )
