from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .core import Member4Detector


DEFAULT_DATASET = Path(__file__).parents[2] / "datasets" / "hydromet" / "member4_hydromet.csv"


@lru_cache(maxsize=1)
def get_member4_detector() -> Member4Detector:
    path = Path(os.getenv("MEMBER4_HYDROMET_CSV_PATH", str(DEFAULT_DATASET)))
    if not path.exists():
        raise RuntimeError(
            f"Member 4 normalized hydromet dataset was not found at {path}. "
            "Run scripts/prepare_member4_hydromet.py before starting the API."
        )
    return Member4Detector.from_csv(path)
