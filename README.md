# contract-clauses-reviewer

Playbook-driven contract clause review. Given a contract and a playbook of
rules, the tool segments the contract into clauses, assesses each rule with a
**grounded verdict** (Entailment / Contradiction / NotMentioned plus the exact
supporting span), verifies and retries low-confidence verdicts, then drafts
redlines and a deviation score for a human to sign off.

Built against an open-source LLM via any OpenAI-compatible endpoint (e.g. a
local [Ollama](https://ollama.com) server) — no agent framework, no paid API.
The core can also run fully offline against a built-in `FakeLLM`.

## How it works

1. **Segment** — contract (text) → clause spans  *(deterministic)*
2. **Match** — locate spans relevant to each playbook rule  *(deterministic)*
3. **Assess** — grounded verdict per rule  *(reasoning)*
4. **Verify & reflect** — re-run verdicts that fail checks  *(reasoning)*
5. **Report** — deviations vs. playbook stance, redlines, score  *(deterministic)*
6. **Human sign-off** — review, approve, route flags

The agent augments a reviewer; it never finalizes on its own.

## Quickstart

Requires **Python 3.11+**.

```bash
# 1. Install (editable, with test deps)
pip install -e ".[dev]"

# 2. Configure the model endpoint
cp .env.example .env          # defaults target local Ollama / qwen2.5:7b

# 3. Run the test suite (hermetic — no model or dataset needed)
pytest -q

# 4. Try it offline, no model required
printf 'The obligations shall survive termination of this Agreement.' > nda.txt
contract-review review --file nda.txt --fake
```

To run against a real model, start Ollama and pull a model, then drop `--fake`:

```bash
ollama pull qwen2.5:7b        # or set LLM_MODEL=qwen2.5:3b on low-RAM machines
contract-review review --file nda.txt
```

## CLI

```bash
contract-review review --file my_nda.txt                 # review a text contract
contract-review review --contractnli-id 3 --split dev    # review a ContractNLI doc
contract-review review --file my_nda.txt --save          # persist to SQLite
contract-review review --file my_nda.txt --fake          # offline, no model
contract-review eval   --split dev --n 10                # score against gold
```

## HTTP service

```bash
uvicorn contract_review.api.app:app --reload
curl -s localhost:8000/reviews -H 'content-type: application/json' \
  -d '{"text": "...contract text...", "use_fake": true}'
```

Endpoints: `POST /reviews`, `GET /reviews`, `GET /reviews/{id}`,
`POST /reviews/{id}/signoff`, `GET /playbooks/{name}`, `GET /health`.
A `Dockerfile` is included for containerized deployment.

## Configuration

Settings are read from environment variables (or a `.env` file); see
`.env.example` and `contract_review/config.py`. Key ones:

| Variable | Default | Purpose |
|---|---|---|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible endpoint |
| `LLM_MODEL` | `qwen2.5:7b` | Model name as the server knows it |
| `LLM_API_KEY` | `not-needed` | Most local servers ignore this |

No paid API or key is required for local use.

## Evaluation dataset

During development the reviewer is scored against **ContractNLI**
(Koreeda & Manning, *Findings of EMNLP 2021*) — 607 NDAs annotated with 17
hypotheses and evidence spans — used as an **evaluation oracle, not for
training** (CC BY 4.0). The dataset is **not** vendored; fetch it locally into
a git-ignored scratch directory:

```bash
bash scripts/fetch_contractnli.sh
contract-review eval --split dev --n 20
```

`eval` reports verdict accuracy, verdict macro-F1, and evidence F1.

## Status

Active development; per-stage status lives in each module's docstring.
