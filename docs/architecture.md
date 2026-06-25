# Architecture

A contract clause reviewer: given one contract and a playbook (rubric), it
produces a grounded, redline-ready review for a human to sign off on. This
document records the system design and the decisions behind it.

## Data spine

Every stage is a transformation over these objects (defined in
`contract_review/models.py`):

```
text -> Document -> RetrievedContext -> Assessment -> VerifiedAssessment -> Report
          (spans)     (per rule)         (verdict +     (checked /            (findings +
                                          evidence)       repaired)             score)
```

## Stages

| # | Stage | In -> Out | Model? |
|---|-------|-----------|--------|
| 1 | Segment | text -> Document(spans) | no |
| 2 | Match | Document, Rule -> RetrievedContext | no |
| 3 | Assess | Rule, RetrievedContext -> Assessment | yes |
| 4 | Verify & reflect | Assessment, Document -> VerifiedAssessment | mostly no |
| 5 | Report | Playbook, [VerifiedAssessment] -> Report | no (LLM for redline text only) |
| 6 | Human sign-off | Report -> approved/edited | person |

The model is called only in stage 3 (and optionally a critique in stage 4).
Everything else is deterministic, by design: autonomy is spent only where
judgment is required.

## Control loop

```
for rule in playbook.rules:                  # 17 rules
    ctx = match(document, rule)
    repeat up to max_assess_attempts:
        a  = assess(rule, ctx)               # two-step: think, then extract
        va = verify(a, document)             # cited spans exist + grounded
    until va.checks_passed
report(playbook, [va...])                    # expected vs actual -> deviations, score
```

## Assess stage (the core)

Two-step, which keeps reasoning and structure separate - especially valuable for
smaller open-source models that struggle to reason and format at once:

1. **Think** - a free-form completion: reasoning over the rule and the ID-tagged
   spans (handles negation-by-exception).
2. **Extract** - a completion that forces the `submit_assessment` tool call,
   turning that reasoning into a structured `{verdict, evidence_span_ids,
   rationale}`.

Evidence is cited by span id (never quoted text) so grounding is mechanically
verifiable.

## Module layout (ports and adapters)

The domain core depends on interfaces (ports), never on concrete I/O. Adapters
implement the ports. This keeps the core testable without an API key and makes
delivery/storage/model swappable.

```
contract_review/
  models.py            # domain types (Pydantic v2)
  config.py            # settings (pydantic-settings)
  ports.py             # interfaces: LLM, DocumentSource, ReviewRepository
  pipeline.py          # orchestration over the ports
  stages/              # segment, match, assess, verify, report (pure domain)
  llm/                 # LLM-port adapters: OpenAI-compatible (open models) + ScriptedLLM
  datasets/            # ContractNLI / PDF adapters implementing DocumentSource
  playbook/            # rubric artifacts + loader
  storage/             # SQLite adapter implementing ReviewRepository
  api/                 # FastAPI delivery adapter
  cli.py               # CLI delivery adapter
evaluation/            # oracle + metrics + harness (ContractNLI gold)
```

## Concurrency and caching

The 17 per-rule assessments are independent and run concurrently (bounded by a
semaphore). With a local model the cost is compute/latency rather than per-token
billing, so concurrency is the main throughput lever.

## Dependencies

Used: `httpx` (calls an OpenAI-compatible LLM endpoint directly - open models via
Ollama/vLLM/etc., no vendor SDK), `pydantic` + `pydantic-settings` (models,
validation, config), `fastapi` + `uvicorn` (service), `pyyaml` (playbook),
SQLite via the stdlib (persistence), `pytest` (tests).

Deliberately avoided: orchestration frameworks (LangChain / LlamaIndex /
CrewAI) - they hide the agent loop this project exists to master, and a fixed
pipeline needs no orchestration engine; vector databases - single-document
long-context review needs no retrieval index; memory frameworks - there is no
conversation, so in-run state is just the accumulating Report.

## Persistence

Reviews are auditable artifacts. They are stored through a `ReviewRepository`
port, implemented on SQLite for v1 (file-based, zero-config) and swappable to
Postgres without touching the core.

## Evaluation

ContractNLI gold annotations are an objective, per-example oracle (not training
data). Metrics: per-class verdict accuracy and macro-F1, evidence-span
precision/recall/F1, and end-to-end deviation-detection accuracy. The harness
runs the pipeline over N documents, scores against gold, and stores runs so
regressions are visible as the system is tuned.

## Delivery and deployment

The CLI and the FastAPI service are thin shells over the same core. The service
is the deployable target; a contract is uploaded, reviewed against a named
playbook, and the report is returned and persisted for sign-off.
```
