"""Run every test exactly once and report duration per logical suite."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
SUITES = [
    ("unit", ["discover", "-s", "tests/unit", "-t", ".", "-q"]),
    ("components", ["discover", "-s", "tests/components", "-t", ".", "-q"]),
    ("pwa-contracts", ["discover", "-s", "tests/pwa", "-t", ".", "-q"]),
    ("e2e/navigation", ["tests.e2e.test_navigation", "-q"]),
    ("e2e/checklist", ["tests.e2e.test_checklist_page", "-q"]),
    ("e2e/favorites", ["tests.e2e.test_favorites_page", "-q"]),
    ("e2e/later", ["tests.e2e.test_later_page", "-q"]),
    ("e2e/history", ["tests.e2e.test_history_page", "-q"]),
    ("e2e/persistence", ["tests.e2e.test_persistence", "-q"]),
    ("e2e/responsive-accessibility", ["tests.e2e.test_responsive_accessibility", "-q"]),
    ("e2e/pwa-runtime", ["tests.e2e.test_pwa_runtime", "-q"]),
]


def test_count(output: str) -> int:
    match = re.search(r"Ran (\d+) tests?", output)
    return int(match.group(1)) if match else 0


def main() -> int:
    environment = os.environ.copy()
    environment["GUMLI_RUN_E2E"] = "1"
    environment.setdefault("GUMLI_HEADLESS", "1")
    results = []

    for name, arguments in SUITES:
        started = time.perf_counter()
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", *arguments],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
        )
        duration = time.perf_counter() - started
        combined = completed.stdout + completed.stderr
        count = test_count(combined)
        status = "OK" if completed.returncode == 0 else "FAIL"
        results.append((name, count, duration, status))
        print(f"{name:<30} {count:>3} tests  {duration:>8.3f} s  {status}", flush=True)
        if completed.returncode:
            print(combined)
            return completed.returncode

    print("-" * 65)
    print(
        f"TOTAL{'':<25} {sum(row[1] for row in results):>3} tests  "
        f"{sum(row[2] for row in results):>8.3f} s  OK"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
