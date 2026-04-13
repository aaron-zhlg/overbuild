from __future__ import annotations

import atexit
import json
import os
import threading
from collections import Counter
from pathlib import Path

_COUNTS: Counter[str] = Counter()
_LOCK = threading.Lock()
_CONFIG_LOCK = threading.Lock()
_DEFAULT_REPORT_FILENAME = "overbuild_report.json"
_DEFAULT_FLUSH_INTERVAL_SECONDS = 10 * 60
_REPORT_PATH: Path = (Path.cwd() / _DEFAULT_REPORT_FILENAME).resolve()
_FLUSH_INTERVAL_SECONDS = float(_DEFAULT_FLUSH_INTERVAL_SECONDS)
_SAVE_TO_LOCAL = True
_REPORTER_STOP = threading.Event()
_REPORTER_THREAD: threading.Thread | None = None


def probe_hit(probe_id: str) -> None:
    with _LOCK:
        _COUNTS[probe_id] += 1


def snapshot() -> dict[str, int]:
    with _LOCK:
        return dict(_COUNTS)


def configure_reporting(
    output_path: str | os.PathLike[str] | None = None,
    flush_interval_seconds: float | None = None,
    save_to_local: bool = True,
) -> None:
    global _REPORT_PATH, _FLUSH_INTERVAL_SECONDS, _SAVE_TO_LOCAL

    if output_path is not None:
        resolved_report_path = Path(output_path).resolve()
    else:
        resolved_report_path = (Path(os.getcwd()) / _DEFAULT_REPORT_FILENAME).resolve()

    interval = (
        float(flush_interval_seconds)
        if flush_interval_seconds is not None
        else float(_DEFAULT_FLUSH_INTERVAL_SECONDS)
    )
    if interval <= 0:
        raise ValueError("flush_interval_seconds must be > 0")

    with _CONFIG_LOCK:
        _REPORT_PATH = resolved_report_path
        _FLUSH_INTERVAL_SECONDS = interval
        _SAVE_TO_LOCAL = save_to_local
        if _SAVE_TO_LOCAL:
            _start_reporter_locked()
        else:
            _REPORTER_STOP.set()


def _start_reporter_locked() -> None:
    global _REPORTER_THREAD
    if _REPORTER_THREAD is not None and _REPORTER_THREAD.is_alive():
        return

    _REPORTER_STOP.clear()
    _REPORTER_THREAD = threading.Thread(
        target=_reporter_loop,
        name="overbuild-reporter",
        daemon=True,
    )
    _REPORTER_THREAD.start()


def _reporter_loop() -> None:
    while True:
        with _CONFIG_LOCK:
            wait_seconds = _FLUSH_INTERVAL_SECONDS
        if _REPORTER_STOP.wait(wait_seconds):
            return
        _write_report(announce=False)


def _write_report(announce: bool) -> None:
    with _CONFIG_LOCK:
        if not _SAVE_TO_LOCAL:
            return
        path = _REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(snapshot(), f, indent=2, sort_keys=True, ensure_ascii=False)
    if announce:
        print(f"[overbuild] wrote report to {path}")


@atexit.register
def dump_report() -> None:
    _REPORTER_STOP.set()
    _write_report(announce=True)
