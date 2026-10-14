#!/usr/bin/env python3
"""Compare fresh query results with golden (reference) numbers.

Usage: check.py golden.json results.json [--today YYYY-MM-DD]
golden : {"cases": [{"id", "label", "expected": number, "tolerance_pct": number,
                     "query": {...free-form spec for Claude...},
                     "date": "YYYY-MM-DD", "window_days": <days>}]}   (date + window_days are optional)
results: {"<case id>": number | null}
Statuses: ok, drift (outside tolerance), missing (no result), expired (the case date left the model window).
Exit code 1 when any case drifts or is missing; 2 for malformed input. Self-check: check.py selftest
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path


def evaluate(golden, results, today):
    rows = []
    for case in golden["cases"]:
        row = {"id": case["id"], "label": case.get("label", ""), "expected": case["expected"]}
        if case.get("date") and case.get("window_days") and (today - date.fromisoformat(case["date"])).days > case["window_days"]:
            rows.append({**row, "status": "expired"})
            continue
        actual = results.get(case["id"])
        if actual is None:
            rows.append({**row, "status": "missing"})
            continue
        expected = case["expected"]
        gap = (actual - expected) / expected * 100 if expected else (0.0 if actual == 0 else float("inf"))
        within = abs(gap) <= case.get("tolerance_pct", 0) + 1e-9  # float noise, not drift
        rows.append({**row, "actual": actual, "gap_pct": round(gap, 3), "tolerance_pct": case.get("tolerance_pct", 0),
                     "status": "ok" if within else "drift"})
    return rows


def as_text(rows):
    lines = [f"{r['status'].upper():8} {r['id']}  {r['label']}" +
             (f"  expected {r['expected']:g}, got {r['actual']:g} ({r['gap_pct']}%, tolerance {r['tolerance_pct']}%)" if "actual" in r else "")
             for r in rows]
    counts = {s: sum(r["status"] == s for r in rows) for s in ("ok", "drift", "missing", "expired")}
    return "\n".join(lines + ["", ", ".join(f"{n} {s}" for s, n in counts.items())])


def selftest():
    golden = {"cases": [{"id": "a", "expected": 100, "tolerance_pct": 1}, {"id": "b", "expected": 100, "tolerance_pct": 0},
                        {"id": "c", "expected": 5}, {"id": "d", "expected": 5, "date": "2031-01-01", "window_days": 28}]}
    rows = {r["id"]: r["status"] for r in evaluate(golden, {"a": 100.5, "b": 101}, date(2031, 6, 1))}
    assert rows == {"a": "ok", "b": "drift", "c": "missing", "d": "expired"}
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        selftest()
        sys.exit(0)
    parser = argparse.ArgumentParser()
    parser.add_argument("golden")
    parser.add_argument("results")
    parser.add_argument("--today", default=date.today().isoformat())
    args = parser.parse_args()
    try:
        outcome = evaluate(json.loads(Path(args.golden).read_text(encoding="utf-8")),
                           json.loads(Path(args.results).read_text(encoding="utf-8")), date.fromisoformat(args.today))
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"error: {error!r}", file=sys.stderr)  # exit 1 stays reserved for drift or missing
        sys.exit(2)
    print(as_text(outcome))
    sys.exit(1 if any(r["status"] in ("drift", "missing") for r in outcome) else 0)
