from __future__ import annotations

import atexit
import json
import os
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_COUNTS: Counter[str] = Counter()
_LOCK = threading.Lock()
_CONFIG_LOCK = threading.Lock()
_DEFAULT_REPORT_DIRNAME = "overbuild_reports"
_REPORT_FILENAME_PREFIX = "overbuild_report_"
_DEFAULT_FLUSH_INTERVAL_SECONDS = 10 * 60
_REPORT_DIR: Path = (Path.cwd() / _DEFAULT_REPORT_DIRNAME).resolve()
_FLUSH_INTERVAL_SECONDS = float(_DEFAULT_FLUSH_INTERVAL_SECONDS)
_SAVE_TO_LOCAL = True
_API_KEY: str | None = None
_REPORTER_STOP = threading.Event()
_REPORTER_THREAD: threading.Thread | None = None


def probe_hit(probe_id: str) -> None:
    with _LOCK:
        _COUNTS[probe_id] += 1


def snapshot() -> dict[str, int]:
    with _LOCK:
        return dict(_COUNTS)


def configure_reporting(
    output_dir: str | os.PathLike[str] | None = None,
    flush_interval_seconds: float | None = None,
    save_to_local: bool = True,
    api_key: str | None = None,
) -> None:
    global _REPORT_DIR, _FLUSH_INTERVAL_SECONDS, _SAVE_TO_LOCAL, _API_KEY

    if output_dir is not None:
        resolved_report_dir = Path(output_dir).resolve()
    else:
        resolved_report_dir = (Path(os.getcwd()) / _DEFAULT_REPORT_DIRNAME).resolve()

    interval = (
        float(flush_interval_seconds)
        if flush_interval_seconds is not None
        else float(_DEFAULT_FLUSH_INTERVAL_SECONDS)
    )
    if interval <= 0:
        raise ValueError("flush_interval_seconds must be > 0")

    with _CONFIG_LOCK:
        _REPORT_DIR = resolved_report_dir
        _FLUSH_INTERVAL_SECONDS = interval
        _SAVE_TO_LOCAL = save_to_local
        _API_KEY = api_key
        if _SAVE_TO_LOCAL or _API_KEY:
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
        save_to_local = _SAVE_TO_LOCAL
        api_key = _API_KEY
        report_dir = _REPORT_DIR
    if not save_to_local and not api_key:
        return

    report = snapshot()

    if save_to_local:
        report_dir.mkdir(parents=True, exist_ok=True)
        path = report_dir / _build_report_filename()
        with path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True, ensure_ascii=False)
        if announce:
            print(f"[overbuild] wrote report to {path}")

    if api_key:
        _report_to_api(api_key=api_key, report=report)


def _build_report_filename() -> str:
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    return f"{_REPORT_FILENAME_PREFIX}{timestamp}.json"


def _report_to_api(api_key: str, report: dict[str, int]) -> None:
    # Reserved API reporting hook. Intentionally left unimplemented for now.
    _ = (api_key, report)


@atexit.register
def dump_report() -> None:
    _REPORTER_STOP.set()
    _write_report(announce=True)
