#!/usr/bin/env python3
"""Decompose a change between two periods by one dimension.

Usage: why.py input.json [--format text|json]
additive: {"metric","unit","kind":"additive","dimension","a_label","b_label",
           "rows":[{"key","a","b"}]}        a = the period being explained, b = the comparison period
ratio:    {"kind":"ratio", ..., "rows":[{"key","a_num","a_den","b_num","b_den"}]}
          rate = num / den; the change of the total rate is split into a rate effect and a mix effect per key
Self-check: why.py selftest
"""
import argparse
import json
import sys
from pathlib import Path

TOP_N = 5


def additive(rows):
    total_a = sum(r["a"] for r in rows)
    total_b = sum(r["b"] for r in rows)
    delta = total_a - total_b
    out = []
    for r in rows:
        d = r["a"] - r["b"]
        out.append({"key": r["key"], "a": r["a"], "b": r["b"], "delta": d,
                    "share_of_change_pct": round(d / delta * 100, 1) if delta else None,
                    "change_pct": round(d / r["b"] * 100, 1) if r["b"] else None})
    out.sort(key=lambda x: -abs(x["delta"]))
    gross = sum(abs(x["delta"]) for x in out)
    return {"total_a": total_a, "total_b": total_b, "delta": delta,
            "top_share_of_gross_pct": round(abs(out[0]["delta"]) / gross * 100, 1) if gross and out else None,
            "rows": out}


def ratio(rows):
    den_a = sum(r["a_den"] for r in rows)
    den_b = sum(r["b_den"] for r in rows)
    if not den_a or not den_b:
        raise ValueError("a period has a zero denominator")
    rate_a = sum(r["a_num"] for r in rows) / den_a
    rate_b = sum(r["b_num"] for r in rows) / den_b
    out = []
    for r in rows:
        w_a, w_b = r["a_den"] / den_a, r["b_den"] / den_b
        r_a = r["a_num"] / r["a_den"] if r["a_den"] else rate_b
        r_b = r["b_num"] / r["b_den"] if r["b_den"] else rate_b  # no base volume: neutral rate
        rate_effect = w_a * (r_a - r_b)
        mix_effect = (w_a - w_b) * (r_b - rate_b)
        out.append({"key": r["key"], "rate_a_pct": round(r_a * 100, 1), "rate_b_pct": round(r_b * 100, 1),
                    "volume_share_a_pct": round(w_a * 100, 1), "volume_share_b_pct": round(w_b * 100, 1),
                    "rate_effect_pp": round(rate_effect * 100, 2), "mix_effect_pp": round(mix_effect * 100, 2),
                    "total_effect_pp": round((rate_effect + mix_effect) * 100, 2)})
    out.sort(key=lambda x: -abs(x["total_effect_pp"]))
    return {"rate_a_pct": round(rate_a * 100, 2), "rate_b_pct": round(rate_b * 100, 2),
            "delta_pp": round((rate_a - rate_b) * 100, 2), "rows": out}


def run(payload):
    kind = payload.get("kind", "additive")
    if kind not in ("additive", "ratio"):
        raise ValueError(f"unknown kind: {kind}")
    body = ratio(payload["rows"]) if kind == "ratio" else additive(payload["rows"])
    return {k: payload.get(k) for k in ("metric", "unit", "dimension", "a_label", "b_label")} | body


def as_text(rep):
    head = f"{rep['metric']} by {rep['dimension']}: {rep['a_label']} vs {rep['b_label']}"
    if "delta_pp" in rep:
        lines = [head, f"rate {rep['rate_b_pct']}% -> {rep['rate_a_pct']}% ({rep['delta_pp']} pp)"]
        lines += [f"- {r['key']}: {r['total_effect_pp']} pp (rate {r['rate_effect_pp']}, mix {r['mix_effect_pp']}); "
                  f"rate {r['rate_b_pct']}% -> {r['rate_a_pct']}%, volume share {r['volume_share_b_pct']}% -> {r['volume_share_a_pct']}%"
                  for r in rep["rows"][:TOP_N]]
        return "\n".join(lines)
    lines = [head, f"total {rep['total_b']:g} -> {rep['total_a']:g} (delta {rep['delta']:g} {rep['unit'] or ''})"]
    lines += [f"- {r['key']}: {r['delta']:g} ({r['share_of_change_pct']}% of the change; {r['change_pct']}% vs before)"
              for r in rep["rows"][:TOP_N]]
    return "\n".join(lines)


def selftest():
    rows = [{"key": "x", "a": 150, "b": 100}, {"key": "y", "a": 50, "b": 50}, {"key": "z", "a": 10, "b": 20}]
    rep = run({"metric": "m", "dimension": "d", "kind": "additive", "rows": rows})
    assert rep["delta"] == 40 and rep["rows"][0]["key"] == "x" and rep["rows"][0]["share_of_change_pct"] == 125.0
    rrows = [{"key": "p", "a_num": 50, "a_den": 100, "b_num": 70, "b_den": 100},
             {"key": "q", "a_num": 90, "a_den": 100, "b_num": 18, "b_den": 20},
             {"key": "n", "a_num": 5, "a_den": 10, "b_num": 0, "b_den": 0}]
    rr = run({"metric": "r", "dimension": "d", "kind": "ratio", "rows": rrows})
    assert abs(sum(r["total_effect_pp"] for r in rr["rows"]) - rr["delta_pp"]) < 0.1  # effects add up to the total change
    assert rr["rows"][0]["key"] == "p"
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        selftest()
        sys.exit(0)
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    try:
        result = run(json.loads(Path(args.input).read_text(encoding="utf-8")))
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"error: {error!r}", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(result, ensure_ascii=False, indent=1) if args.format == "json" else as_text(result))
