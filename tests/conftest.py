import sys
from pathlib import Path

import pytest

# Make the project root importable so `contract_review` and `evaluation` resolve
# even when pytest is run from elsewhere.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def fixtures_data_dir() -> Path:
    """A tiny ContractNLI-format dataset so tests don't need the real download."""
    return Path(__file__).parent / "fixtures" / "contractnli"
