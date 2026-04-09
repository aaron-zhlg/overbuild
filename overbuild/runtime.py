from __future__ import annotations

import atexit
import json
import os
import threading
from collections import Counter
from pathlib import Path

_COUNTS: Counter[str] = Counter()
_LOCK = threading.Lock()


def probe_hit(probe_id: str) -> None:
    with _LOCK:
        _COUNTS[probe_id] += 1


def snapshot() -> dict[str, int]:
    with _LOCK:
        return dict(_COUNTS)


def _report_path() -> Path:
    raw = os.getenv("OVERBUILD_REPORT", "overbuild_report.json")
    return Path(raw).resolve()


@atexit.register
def dump_report() -> None:
    path = _report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(snapshot(), f, indent=2, sort_keys=True, ensure_ascii=False)
    print(f"[overbuild] wrote report to {path}")
