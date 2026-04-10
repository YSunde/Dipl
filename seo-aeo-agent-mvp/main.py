from __future__ import annotations

from pathlib import Path
from pprint import pprint

from app.orchestrator import SeoAeoOrchestrator


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    summary = SeoAeoOrchestrator(str(root)).run()
    pprint(summary)
