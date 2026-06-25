"""Command-line entrypoint.

  contract-review review --file contract.txt [--playbook nda_contractnli] [--offline]
  contract-review review --contractnli-id 3 [--split dev] [--offline] [--save]
  contract-review eval --split dev --n 5 [--offline]

--offline uses the deterministic ScriptedLLM (no model/network); otherwise the
OpenAI-compatible adapter is used (a local Ollama server by default).
"""

from __future__ import annotations

import argparse
import sys

from .config import load_settings
from .datasets.contractnli import load_documents
from .llm import OpenAICompatibleLLM, ScriptedLLM
from .models import Assessment, Document, Playbook, Report
from .pipeline import review as run_pipeline
from .playbook.loader import load_named
from .stages.segment import segment


def _build_llm(offline: bool, settings):
    return ScriptedLLM() if offline else OpenAICompatibleLLM(settings)


def _load_document(args) -> Document:
    if args.file:
        text = open(args.file, encoding="utf-8").read()
        return segment(text, source_name=args.file, doc_id=args.file)
    if args.contractnli_id is not None:
        for doc in load_documents(args.split):
            if doc.id == str(args.contractnli_id):
                return doc
        raise SystemExit(f"document id {args.contractnli_id} not found in {args.split} split")
    raise SystemExit("provide either --file or --contractnli-id")


def format_report(report: Report, playbook: Playbook) -> str:
    lines = [
        f"Contract: {report.document_id}    Playbook: {report.playbook_id}",
        f"{report.summary}",
        f"Deviation score: {report.deviation_score:.0%}",
        "-" * 72,
    ]
    for finding in report.findings:
        mark = "DEVIATION" if finding.is_deviation else "ok"
        lines.append(
            f"[{finding.rule_id:7}] {finding.rule_name[:34]:34} "
            f"expected={finding.expected.value:13} actual={finding.actual.value:13} {mark}"
        )
        if finding.is_deviation and finding.suggested_redline:
            lines.append(f"          redline: {finding.suggested_redline}")
    return "\n".join(lines)


def cmd_review(args) -> int:
    settings = load_settings()
    document = _load_document(args)
    playbook = load_named(args.playbook)
    llm = _build_llm(args.offline, settings)
    report = run_pipeline(document, playbook, llm, settings=settings)
    print(format_report(report, playbook))
    if args.save:
        from .storage import SQLiteReviewRepository

        review_id = SQLiteReviewRepository(args.db).save(report)
        print(f"\nsaved review {review_id} to {args.db}")
    return 0


def cmd_eval(args) -> int:
    from evaluation.metrics import evaluate
    from evaluation.oracle import load_gold

    settings = load_settings()
    playbook = load_named(args.playbook)
    documents = load_documents(args.split)[: args.n]
    gold = load_gold(args.split)
    llm = _build_llm(args.offline, settings)

    pairs = []
    for document in documents:
        # eval scores verdicts/evidence only; skip the extra redline calls.
        report = run_pipeline(document, playbook, llm, settings=settings, with_redlines=False)
        gold_doc = gold.get(document.id, {})
        for finding in report.findings:
            if finding.rule_id in gold_doc:
                pairs.append(
                    (
                        Assessment(
                            rule_id=finding.rule_id,
                            verdict=finding.actual,
                            evidence_span_ids=finding.evidence_span_ids,
                        ),
                        gold_doc[finding.rule_id],
                    )
                )

    result = evaluate(pairs)
    print(f"Evaluated {len(documents)} document(s), {result.n} (rule, doc) pairs:")
    print(f"  verdict accuracy : {result.verdict_accuracy:.3f}")
    print(f"  verdict macro-F1 : {result.verdict_macro_f1:.3f}")
    print(f"  evidence P/R/F1  : {result.evidence_precision:.3f} / "
          f"{result.evidence_recall:.3f} / {result.evidence_f1:.3f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="contract-review")
    sub = parser.add_subparsers(dest="command", required=True)

    r = sub.add_parser("review", help="review one contract against a playbook")
    r.add_argument("--file", help="path to a plain-text contract")
    r.add_argument("--contractnli-id", help="review a ContractNLI document by id")
    r.add_argument("--split", default="dev")
    r.add_argument("--playbook", default="nda_contractnli")
    r.add_argument("--offline", action="store_true", help="use the ScriptedLLM (no model)")
    r.add_argument("--save", action="store_true", help="persist the review")
    r.add_argument("--db", default="reviews.db")
    r.set_defaults(func=cmd_review)

    e = sub.add_parser("eval", help="evaluate against ContractNLI gold")
    e.add_argument("--split", default="dev")
    e.add_argument("--n", type=int, default=5)
    e.add_argument("--playbook", default="nda_contractnli")
    e.add_argument("--offline", action="store_true")
    e.set_defaults(func=cmd_eval)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
