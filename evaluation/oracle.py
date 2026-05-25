"""ContractNLI evaluation oracle.

Status: stub. Loads ContractNLI gold annotations and compares the agent's verdict
and evidence spans per (document, rule) against them — the objective, per-example
check. Not training; an answer key. Implemented in a later step.
"""

from __future__ import annotations
