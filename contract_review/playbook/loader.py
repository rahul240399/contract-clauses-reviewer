"""Load and validate playbook artifacts (YAML) into Playbook objects.

The loader is the only thing that knows the on-disk playbook format, so the rest
of the codebase depends on the Playbook dataclass, not YAML. Validation is strict
and fails loudly: a malformed playbook is a configuration error worth surfacing
immediately, not silently dropping rules.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from ..models import Playbook, Rule, Verdict

_PLAYBOOK_DIR = Path(__file__).parent
_REQUIRED_RULE_KEYS = ("id", "name", "statement", "expected_disposition")


def load_playbook(path: str | Path) -> Playbook:
    """Load a playbook from an explicit YAML path."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"playbook not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _build(data, source=str(path))


def load_named(name: str) -> Playbook:
    """Load a bundled playbook by name, e.g. 'nda_contractnli'."""
    return load_playbook(_PLAYBOOK_DIR / f"{name}.yaml")


def _to_verdict(value: object, *, source: str, rule_id: str) -> Verdict:
    try:
        return Verdict(str(value))
    except ValueError:
        allowed = [v.value for v in Verdict]
        raise ValueError(
            f"{source}: rule {rule_id!r} has invalid expected_disposition "
            f"{value!r}; must be one of {allowed}"
        )


def _build(data: object, *, source: str) -> Playbook:
    if not isinstance(data, dict):
        raise ValueError(f"{source}: top-level YAML must be a mapping")
    for key in ("id", "name", "rules"):
        if key not in data:
            raise ValueError(f"{source}: missing required key {key!r}")

    rules: list[Rule] = []
    seen: set[str] = set()
    for index, raw in enumerate(data["rules"]):
        if not isinstance(raw, dict):
            raise ValueError(f"{source}: rule #{index} must be a mapping")
        for key in _REQUIRED_RULE_KEYS:
            if key not in raw:
                raise ValueError(f"{source}: rule #{index} missing required key {key!r}")
        rule_id = str(raw["id"])
        if rule_id in seen:
            raise ValueError(f"{source}: duplicate rule id {rule_id!r}")
        seen.add(rule_id)
        rules.append(
            Rule(
                id=rule_id,
                name=str(raw["name"]),
                statement=str(raw["statement"]),
                expected_disposition=_to_verdict(
                    raw["expected_disposition"], source=source, rule_id=rule_id
                ),
            )
        )

    if not rules:
        raise ValueError(f"{source}: playbook has no rules")

    return Playbook(id=str(data["id"]), name=str(data["name"]), rules=tuple(rules))
