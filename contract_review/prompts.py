"""Prompts and the tool schema for the assess stage.

Kept in one place so they can be tuned (the main lever on assess quality) without
touching stage logic.
"""

from __future__ import annotations

from .models import RetrievedContext, Rule, Verdict

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
