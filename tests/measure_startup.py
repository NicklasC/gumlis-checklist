"""Measure cold and warm PWA startup milestones in isolated Chromium contexts."""

from __future__ import annotations

import argparse
import json
from statistics import median

from playwright.sync_api import sync_playwright

from tests.support.browser_case import PwaServer


FINAL_MILESTONE = "checklist-visible"
WAIT_FOR_FINAL_MILESTONE = (
    "() => Boolean(window.gumliStartup?.snapshot()?.['checklist-visible'])"
)


def startup_marks(page, url: str, *, reload: bool = False) -> dict[str, float]:
    if reload:
        page.reload(wait_until="domcontentloaded")
    else:
        page.goto(url, wait_until="domcontentloaded")
    page.wait_for_function(WAIT_FOR_FINAL_MILESTONE, timeout=90_000)
    marks = page.evaluate("() => window.gumliStartup.snapshot()")
    if FINAL_MILESTONE not in marks:
        raise RuntimeError(f"Missing startup milestone: {FINAL_MILESTONE}")
    return marks


def summarize(samples: list[dict[str, float]]) -> dict[str, float]:
    milestones = sorted(set.intersection(*(set(sample) for sample in samples)))
    return {
        milestone: round(median(sample[milestone] for sample in samples), 1)
        for milestone in milestones
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=3)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("--samples must be at least 1")

    cold_samples: list[dict[str, float]] = []
    warm_samples: list[dict[str, float]] = []

    with PwaServer() as server, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for _ in range(args.samples):
                context = browser.new_context(viewport={"width": 410, "height": 820})
                page = context.new_page()
                cold_samples.append(startup_marks(page, server.base_url))
                warm_samples.append(startup_marks(page, server.base_url, reload=True))
                context.close()
        finally:
            browser.close()

    result = {
        "samples": args.samples,
        "cold": {"median_ms": summarize(cold_samples), "runs": cold_samples},
        "warm": {"median_ms": summarize(warm_samples), "runs": warm_samples},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
