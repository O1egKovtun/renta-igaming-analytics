#!/usr/bin/env python3
"""Flag unusual days: latest day vs the same weekday in the previous 4 weeks (robust z-score).

Usage: anomalies.py input.json [--z 3] [--rel-pct 15] [--max-lag 2] [--format text|json]
input: {"metrics": [{"name", "unit", "dates": ["YYYY-MM-DD", ...], "values": [...]}],
        "freshness": [{"model": "...", "max_date": "YYYY-MM-DD"}], "as_of": "YYYY-MM-DD"}
The latest date of each metric must be a full day. Flags need BOTH |z| >= --z and a relative gap >= --rel-pct percent; the one exception is a non-zero value over an all-zero baseline (flag with baseline_zero true).
Self-check: anomalies.py selftest
"""
import argparse
import json
import math
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path

MAD_TO_SIGMA = 1.4826
MIN_SAME_WEEKDAY_POINTS = 3
SCALE_FLOOR_SHARE = 1 / 20  # keeps a tiny spread from turning a normal wobble into a huge z


def analyse(metric, z_min, rel_min_pct, as_of=None):
    if len(metric["dates"]) != len(metric["values"]):
        raise ValueError(f"{metric['name']}: {len(metric['dates'])} dates vs {len(metric['values'])} values")
    points = {d: v for d, v in zip(metric["dates"], metric["values"])
              if v is not None and math.isfinite(v) and (as_of is None or d <= as_of)}
    if not points:
        return {"name": metric["name"], "status": "no_data"}
    last = max(points)
    last_day = date.fromisoformat(last)
    history = [points.get((last_day - timedelta(days=7 * k)).isoformat()) for k in range(1, 5)]
    history = [v for v in history if v is not None]
    row = {"name": metric["name"], "unit": metric.get("unit", ""), "date": last, "value": points[last]}
    if len(history) < MIN_SAME_WEEKDAY_POINTS:
        return {**row, "status": "insufficient_history", "history_points": len(history)}
    median = statistics.median(history)
    mad = statistics.median([abs(v - median) for v in history])
    scale = max(MAD_TO_SIGMA * mad, SCALE_FLOOR_SHARE * abs(median))
    last_week = points.get((last_day - timedelta(days=7)).isoformat())
    rel = (points[last] - median) / median if median else None
    z = (points[last] - median) / scale if scale else None
    flag = None
    baseline_zero = median == 0 and mad == 0 and points[last] != 0
    if baseline_zero:
        flag = "high" if points[last] > 0 else "low"
    elif z is not None and rel is not None and abs(z) >= z_min and abs(rel) * 100 >= rel_min_pct:
        flag = "high" if z > 0 else "low"
    return {**row, "status": "ok", "baseline_median": median, "history_points": len(history),
            "vs_baseline_pct": None if rel is None else round(rel * 100, 1),
            "vs_last_week_pct": None if not last_week else round((points[last] - last_week) / last_week * 100, 1),
            "z": None if z is None else round(z, 1), "flag": flag, "baseline_zero": baseline_zero}


def stale(freshness, as_of, max_lag):
    out = []
    for item in freshness:
        if item.get("max_date") is None:  # a model with no date at all counts as stale
            out.append({"model": item["model"], "max_date": None, "lag_days": None})
            continue
        lag = (date.fromisoformat(as_of) - date.fromisoformat(item["max_date"])).days
        if lag > max_lag:
            out.append({"model": item["model"], "max_date": item["max_date"], "lag_days": lag})
    return out


def run(payload, z_min=3.0, rel_min_pct=15, max_lag=2):
    results = [analyse(m, z_min, rel_min_pct, payload.get("as_of")) for m in payload["metrics"]]
    as_of = payload.get("as_of") or max((r["date"] for r in results if "date" in r), default=None)
    return {"as_of": as_of, "metrics": results,
            "flags": [r for r in results if r.get("flag")],
            "stale_models": stale(payload.get("freshness", []), as_of, max_lag) if as_of else []}


def as_text(report):
    lines = [f"as of {report['as_of']} (UTC)"]
    for r in report["metrics"]:
        if r["status"] != "ok":
            lines.append(f"- {r['name']}: {r['status']}")
            continue
        mark = {"high": "  << HIGH", "low": "  << LOW"}.get(r["flag"], "")
        lines.append(f"- {r['name']}: {r['value']:g} {r['unit']} | vs same weekday median {r['vs_baseline_pct']}% "
                     f"| vs last week {r['vs_last_week_pct']}% | z {r['z']}{mark}")
    for s in report["stale_models"]:
        lines.append(f"- STALE: {s['model']} ends {s['max_date']} ({s['lag_days']} days behind)")
    return "\n".join(lines)


def selftest():
    dates = [(date(2031, 1, 1) + timedelta(days=i)).isoformat() for i in range(35)]
    values = [100 + (i % 7) for i in range(35)]
    ok = run({"metrics": [{"name": "m", "unit": "", "dates": dates, "values": values}]})
    assert ok["flags"] == [] and ok["metrics"][0]["status"] == "ok"
    spike = run({"metrics": [{"name": "m", "unit": "", "dates": dates, "values": values[:-1] + [250]}],
                 "freshness": [{"model": "x", "max_date": "2031-01-20"}]})
    assert spike["flags"][0]["flag"] == "high" and spike["stale_models"][0]["lag_days"] > 2
    short = run({"metrics": [{"name": "m", "unit": "", "dates": dates[-5:], "values": values[-5:]}]})
    assert short["metrics"][0]["status"] == "insufficient_history"
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        selftest()
        sys.exit(0)
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--z", type=float, default=3.0)
    parser.add_argument("--rel-pct", type=float, default=15)
    parser.add_argument("--max-lag", type=int, default=2)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    try:
        result = run(json.loads(Path(args.input).read_text(encoding="utf-8")), args.z, args.rel_pct, args.max_lag)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"error: {error!r}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(result, ensure_ascii=False, indent=1) if args.format == "json" else as_text(result))
