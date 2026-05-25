# contract-clauses-reviewer

Playbook-driven contract clause review. Given a contract and a playbook of
rules, the tool segments the contract into clauses, assesses each rule against
the contract with a **grounded verdict** (Entailment / Contradiction /
NotMentioned plus the exact supporting span), verifies and retries
low-confidence verdicts, then drafts redlines and a deviation score for a human
to sign off.

Built from scratch on the Anthropic SDK — no agent framework.

## Workflow

1. **Segment** — contract (PDF/text) → clause spans  *(deterministic)*
2. **Match** — locate the spans relevant to each playbook rule  *(deterministic)*
3. **Assess** — grounded verdict per rule  *(reasoning)*
4. **Verify & reflect** — re-run verdicts that fail checks  *(reasoning)*
5. **Report** — deviations vs. playbook stance, redlines, score  *(deterministic)*
6. **Human sign-off** — review, approve, route flags

The agent augments a reviewer; it never finalizes on its own.

## Status

Early development. Per-stage status lives in each module's docstring.

## Development dataset

During development the reviewer is exercised against **ContractNLI**
(Koreeda & Manning, *Findings of EMNLP 2021*) — 607 NDAs annotated with 17
hypotheses and evidence spans — used here as an **evaluation oracle, not for
training**. ContractNLI is released under CC BY 4.0. The dataset is **not**
vendored in this repository; it is fetched locally into an ignored scratch
directory.

## Requirements

- Python 3.11+
- `ANTHROPIC_API_KEY` in the environment (needed by the assess/verify stages)

## Install

    pip install -e .

## Usage (coming as stages land)

    contract-review review <contract.txt> --playbook nda_contractnli
    contract-review eval --split dev --n 10
