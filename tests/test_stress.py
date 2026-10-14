#!/usr/bin/env python3
"""Adversarial stress and use-case tests for anomalies.py, why.py, check.py and build_report.py.

Usage: python3 tests/test_stress.py
All data is synthetic (fictional year 2031), offline, stdlib only.
Tests marked KNOWN BUG document a real defect in a script: they keep asserting the correct
behaviour, and the runner reports them as KNOWN BUG instead of failing the run. When the
script is fixed the runner prints FIXED so the marker can be removed.
"""
import html.parser
import importlib.util
import json
import math
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = [sys.executable, "-I"]
ANOMALIES = ROOT / "scripts" / "anomalies.py"
WHY = ROOT / "scripts" / "why.py"
CHECK = ROOT / "scripts" / "check.py"
VISUALS = ROOT / "skills" / "renta-visuals"
BUILD = VISUALS / "scripts" / "build_report.py"
START = date(2031, 1, 1)
LAST_DAY = START + timedelta(days=34)


def known_bug(severity):
    def mark(fn):
        fn.known_bug = severity
        return fn
    return mark


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(args, env=None):
    return subprocess.run(PY + [str(a) for a in args], capture_output=True, text=True, env=env)


def write(tmp, name, obj):
    path = Path(tmp) / name
    path.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")
    return path


def iso(offset, start=START):
    return (start + timedelta(days=offset)).isoformat()


def metric(values, name="m", unit="", start=START):
    return {"name": name, "unit": unit, "dates": [iso(i, start) for i in range(len(values))], "values": list(values)}


def weekly(days=35, base=100):
    return [base + (i % 7) for i in range(days)]


# ---------------------------------------------------------------- anomalies

def anomalies(payload, *flags):
    """Run anomalies.py on a payload (dict, or raw text); returns (process, parsed json or None)."""
    with tempfile.TemporaryDirectory() as tmp:
        src = write(tmp, "in.json", payload)
        result = run([ANOMALIES, src, "--format", "json", *flags])
    try:
        return result, json.loads(result.stdout)
    except ValueError:
        return result, None


def first_metric(payload, *flags):
    result, out = anomalies(payload, *flags)
    assert result.returncode == 0 and out, result.stderr
    assert "Traceback" not in result.stderr
    return out["metrics"][0]


def test_anomalies_history_boundary_three_weeks():
    short = first_metric({"metrics": [metric(weekly(21))]})
    assert short["status"] == "insufficient_history" and short["history_points"] == 2
    enough = first_metric({"metrics": [metric(weekly(22))]})
    assert enough["status"] == "ok" and enough["history_points"] == 3


def test_anomalies_single_point_and_empty_series():
    assert first_metric({"metrics": [metric([5])]})["status"] == "insufficient_history"
    assert first_metric({"metrics": [metric([])]})["status"] == "no_data"
    assert first_metric({"metrics": [metric([None, None, None])]})["status"] == "no_data"


def test_anomalies_constant_series_threshold_is_inclusive():
    flat = [100] * 34
    assert first_metric({"metrics": [metric(flat + [100])]})["flag"] is None
    assert first_metric({"metrics": [metric(flat + [114])]})["flag"] is None
    assert first_metric({"metrics": [metric(flat + [115])]})["flag"] == "high"
    assert first_metric({"metrics": [metric(flat + [85])]})["flag"] == "low"


def test_anomalies_constant_zero_series_does_not_divide_by_zero():
    row = first_metric({"metrics": [metric([0] * 35)]})
    assert row["status"] == "ok" and row["flag"] is None


def test_anomalies_spike_from_zero_baseline_is_flagged():
    row = first_metric({"metrics": [metric([0] * 34 + [500])]})
    assert row["flag"] == "high", row


def test_anomalies_negative_values_flag_direction():
    flat = [-100] * 34
    assert first_metric({"metrics": [metric(flat + [-2 * 100])]})["flag"] == "low"
    assert first_metric({"metrics": [metric(flat + [-50])]})["flag"] == "high"
    assert first_metric({"metrics": [metric(flat + [-100])]})["flag"] is None


def test_anomalies_none_values_are_skipped_not_fatal():
    values = weekly()
    values[20] = None
    values[-1] = 106
    row = first_metric({"metrics": [metric(values)]})
    assert row["status"] == "ok" and row["history_points"] == 3 and row["flag"] is None
    values[-1] = None  # the latest non-null point becomes the analysed day
    row = first_metric({"metrics": [metric(values)]})
    assert row["date"] == iso(33)


def test_anomalies_nan_and_infinity_never_crash():
    for position, token in ((34, "NaN"), (34, "Infinity"), (34, "-Infinity"), (27, "NaN"), (27, "Infinity")):
        result, out = anomalies(raw_with_token(weekly(), position, token))
        assert result.returncode == 0 and out is not None, (token, position, result.stderr)
        assert "Traceback" not in result.stderr
    assert first_metric(raw_with_token(weekly(), 34, "NaN"))["flag"] is None, "a NaN value must never be flagged"


def raw_with_token(values, position, token):
    items = [str(v) for v in values]
    items[position] = token
    m = metric(values)
    return ('{"metrics": [{"name": "m", "unit": "", "dates": ' + json.dumps(m["dates"]) +
            ', "values": [' + ", ".join(items) + "]}]}")


def test_anomalies_nan_in_history_behaves_like_missing_value():
    spike = weekly()
    spike[-1] = 300
    with_none = spike[:20] + [None] + spike[21:]
    expected = first_metric({"metrics": [metric(with_none)]})
    assert expected["flag"] == "high"
    got = first_metric(raw_with_token(spike, 20, "NaN"))
    assert got["flag"] == expected["flag"], got


def test_anomalies_unsorted_input_matches_sorted_input():
    values = weekly()
    values[-1] = 300
    m = metric(values)
    pairs = list(zip(m["dates"], m["values"]))
    random.Random(3).shuffle(pairs)
    shuffled = {**m, "dates": [p[0] for p in pairs], "values": [p[1] for p in pairs]}
    assert first_metric({"metrics": [shuffled]}) == first_metric({"metrics": [m]})


def test_anomalies_duplicate_dates_do_not_crash():
    m = metric(weekly())
    m["dates"].append(m["dates"][-1])
    m["values"].append(999)
    row = first_metric({"metrics": [m]})
    assert row["date"] == iso(34)


def test_anomalies_gapped_history_is_insufficient_not_wrong():
    m = metric(weekly())
    for drop in (27, 20):  # remove two of the four same-weekday points
        m["values"][drop] = None
    assert first_metric({"metrics": [m]})["status"] == "insufficient_history"


def test_anomalies_future_dated_point_is_not_the_analysed_day():
    values = weekly()
    row = first_metric({"metrics": [metric(values)], "as_of": iso(30)})
    assert row.get("date", iso(30)) <= iso(30), row


def test_anomalies_huge_values_do_not_crash():
    for values in ([10 ** 30] * 35, [1e300] * 34 + [1e308], [1e308, -1e308] * 17 + [1e308], [10 ** 30] * 34 + [5]):
        result, out = anomalies({"metrics": [metric(values)]})
        assert result.returncode == 0 and out is not None, (values[-1], result.stderr)
        assert "Traceback" not in result.stderr


def test_anomalies_freshness_lag_at_and_over_the_limit():
    payload = {"metrics": [metric(weekly())], "as_of": iso(40),
               "freshness": [{"model": "at", "max_date": iso(38)}, {"model": "over", "max_date": iso(37)},
                             {"model": "future", "max_date": iso(60)}]}
    _, out = anomalies(payload)
    assert [s["model"] for s in out["stale_models"]] == ["over"] and out["stale_models"][0]["lag_days"] == 3
    _, out = anomalies(payload, "--max-lag", "0")
    assert sorted(s["model"] for s in out["stale_models"]) == ["at", "over"]
    _, out = anomalies(payload, "--max-lag", "3")
    assert out["stale_models"] == []


def test_anomalies_freshness_with_null_max_date_is_reported_not_crash():
    result, _ = anomalies({"metrics": [metric(weekly())], "freshness": [{"model": "empty", "max_date": None}]})
    assert "Traceback" not in result.stderr, result.stderr


def test_anomalies_empty_metrics_list():
    result, out = anomalies({"metrics": []})
    assert result.returncode == 0 and out["metrics"] == [] and out["flags"] == []
    text = run([ANOMALIES, "-"]).returncode  # a missing file is an error, not a crash loop
    assert text != 0


def test_anomalies_malformed_input_fails_nonzero_with_a_message():
    bad_inputs = ["not json", "", '{"metrics": [', "[]", "{}", '{"metrics": [{"name": "m"}]}',
                  '{"metrics": [{"name": "m", "dates": ["nope"], "values": [1]}]}',
                  '{"metrics": [{"name": "m", "dates": ["2031-13-45"], "values": [1]}]}']
    for text in bad_inputs:
        result, out = anomalies(text)
        assert result.returncode != 0 and out is None, (text, result.stdout)
        assert result.stderr.strip(), f"no message for {text!r}"


def test_anomalies_malformed_json_has_no_traceback():
    result, _ = anomalies("not json")
    assert result.returncode != 0 and "Traceback" not in result.stderr, result.stderr


def test_anomalies_dates_values_length_mismatch_is_rejected():
    m = metric(weekly())
    m["values"] = m["values"][:-3]
    result, _ = anomalies({"metrics": [m]})
    assert result.returncode != 0, "mismatched dates/values accepted silently"


def test_anomalies_flag_requires_both_z_and_relative_gap_cli():
    spread = [50, 150] * 17 + [50]  # high spread: big relative gap, small z
    spread[-1] = 140
    assert first_metric({"metrics": [metric(spread[:-1] + [140])]})["flag"] is None
    flat = [100] * 34
    assert first_metric({"metrics": [metric(flat + [130])]}, "--rel-pct", "50")["flag"] is None  # big z, small gap
    assert first_metric({"metrics": [metric(flat + [130])]}, "--z", "9")["flag"] is None          # big gap, small z
    assert first_metric({"metrics": [metric(flat + [130])]}, "--z", "5", "--rel-pct", "25")["flag"] == "high"


def test_anomalies_never_flags_without_both_conditions_fuzz():
    module = load_module(ANOMALIES, "anomalies_under_test")
    rng = random.Random(11)
    flagged = 0
    for _ in range(400):
        base = rng.choice([1, 10, 100, 5000])
        noise = rng.choice([0, 1, 5, 30])
        days = rng.randint(22, 60)
        values = [max(0, base + rng.randint(-noise, noise) * base // 100) if rng.random() > 5e-2 else None
                  for _ in range(days)]
        values[-1] = int(base * rng.choice([0, 1, 1, 2, 3, 10]))
        z_min, rel_min = rng.choice([(3.0, 15), (2.0, 5), (5.0, 50), (1.0, 1)])
        row = module.analyse(metric(values), z_min, rel_min)
        if row.get("flag") and not row.get("baseline_zero"):  # an all-zero baseline is the documented exception
            flagged += 1
            assert row["z"] is not None and row["vs_baseline_pct"] is not None, row
            assert abs(row["z"]) >= z_min - 6e-2, row
            assert abs(row["vs_baseline_pct"]) >= rel_min - 6e-2, row
            assert (row["flag"] == "high") == (row["z"] > 0), row
    assert flagged > 0, "fuzz never produced a flag: it proves nothing"


def test_anomalies_text_format_handles_unicode_and_missing_status():
    payload = {"metrics": [metric(weekly(), name="café 中文", unit="€"), metric([], name="empty")]}
    with tempfile.TemporaryDirectory() as tmp:
        result = run([ANOMALIES, write(tmp, "in.json", payload)])
    assert result.returncode == 0 and "empty: no_data" in result.stdout, result.stderr


# ---------------------------------------------------------------- why

def why(payload, *flags):
    with tempfile.TemporaryDirectory() as tmp:
        result = run([WHY, write(tmp, "in.json", payload), "--format", "json", *flags])
    try:
        return result, json.loads(result.stdout)
    except ValueError:
        return result, None


def additive_payload(rows):
    return {"metric": "m", "unit": "u", "kind": "additive", "dimension": "d", "a_label": "A", "b_label": "B", "rows": rows}


def ratio_payload(rows):
    return {**additive_payload(rows), "kind": "ratio"}


def good_why(payload):
    result, out = why(payload)
    assert result.returncode == 0 and out is not None, result.stderr
    return out


def test_why_zero_baseline_does_not_divide_by_zero():
    out = good_why(additive_payload([{"key": "new", "a": 50, "b": 0}, {"key": "old", "a": 10, "b": 10}]))
    new = next(r for r in out["rows"] if r["key"] == "new")
    assert new["change_pct"] is None and new["share_of_change_pct"] == 100.0
    out = good_why(additive_payload([{"key": "x", "a": 0, "b": 0}]))
    assert out["delta"] == 0 and out["rows"][0]["share_of_change_pct"] is None


def test_why_all_equal_periods():
    out = good_why(additive_payload([{"key": k, "a": 7, "b": 7} for k in "abc"]))
    assert out["delta"] == 0 and out["top_share_of_gross_pct"] is None
    assert all(r["delta"] == 0 and r["share_of_change_pct"] is None for r in out["rows"])
    out = good_why(ratio_payload([{"key": k, "a_num": 3, "a_den": 10, "b_num": 3, "b_den": 10} for k in "ab"]))
    assert out["delta_pp"] == 0 and all(r["total_effect_pp"] == 0 for r in out["rows"])


def test_why_single_key_and_empty_rows():
    out = good_why(additive_payload([{"key": "only", "a": 30, "b": 10}]))
    assert out["rows"][0]["share_of_change_pct"] == 100.0 and out["top_share_of_gross_pct"] == 100.0
    out = good_why(additive_payload([]))
    assert out["rows"] == [] and out["delta"] == 0
    with tempfile.TemporaryDirectory() as tmp:
        text = run([WHY, write(tmp, "in.json", additive_payload([{"key": "k", "a": 1, "b": 0}]))])
    assert text.returncode == 0 and "k:" in text.stdout, text.stderr


def test_why_one_sided_keys_additive():
    out = good_why(additive_payload([{"key": "gone", "a": 0, "b": 40}, {"key": "born", "a": 40, "b": 0},
                                     {"key": "same", "a": 5, "b": 5}]))
    assert out["delta"] == 0
    assert {r["key"]: r["change_pct"] for r in out["rows"]}["gone"] == -100.0
    assert out["top_share_of_gross_pct"] == 50.0


def test_why_negative_contributions_and_sorting():
    rows = [{"key": "a", "a": -30, "b": 10}, {"key": "b", "a": 5, "b": -20}, {"key": "c", "a": 3, "b": 2}]
    out = good_why(additive_payload(rows))
    assert [r["key"] for r in out["rows"]] == ["a", "b", "c"]
    assert out["rows"][0]["delta"] == -40
    assert abs(sum(r["delta"] for r in out["rows"]) - out["delta"]) < 1e-9


def test_why_additive_identity_fuzz():
    module = load_module(WHY, "why_under_test")
    rng = random.Random(5)
    for _ in range(300):
        rows = [{"key": f"k{i}", "a": rng.uniform(-900, 900) * rng.choice([0, 1, 1]), "b": rng.uniform(-900, 900) * rng.choice([0, 1, 1])}
                for i in range(rng.randint(1, 12))]
        out = module.run(additive_payload(rows))
        assert abs(sum(r["delta"] for r in out["rows"]) - out["delta"]) < 1e-9
        assert abs(out["total_a"] - sum(r["a"] for r in rows)) < 1e-9
        if out["delta"]:
            assert abs(sum(r["share_of_change_pct"] for r in out["rows"]) - 100) < 5e-2 * len(rows) + 1e-1


def test_why_ratio_effects_add_up_to_total_change_fuzz():
    module = load_module(WHY, "why_ratio_under_test")
    rng = random.Random(9)
    for _ in range(300):
        rows = []
        for i in range(rng.randint(1, 8)):
            a_den, b_den = rng.choice([0, 1, 50, 400]), rng.choice([0, 1, 50, 400])
            rows.append({"key": f"k{i}", "a_num": a_den * rng.random(), "a_den": a_den,
                         "b_num": b_den * rng.random(), "b_den": b_den})
        if not sum(r["a_den"] for r in rows) or not sum(r["b_den"] for r in rows):
            continue
        out = module.run(ratio_payload(rows))
        total = sum(r["total_effect_pp"] for r in out["rows"])
        assert abs(total - out["delta_pp"]) <= 5e-3 * (len(rows) + 1) + 1e-2, (total, out["delta_pp"])
        for r in out["rows"]:
            assert abs(r["rate_effect_pp"] + r["mix_effect_pp"] - r["total_effect_pp"]) <= 11e-3


def test_why_ratio_one_sided_zero_denominator_per_key():
    rows = [{"key": "base", "a_num": 5, "a_den": 10, "b_num": 6, "b_den": 10},
            {"key": "new", "a_num": 4, "a_den": 10, "b_num": 0, "b_den": 0},
            {"key": "lost", "a_num": 0, "a_den": 0, "b_num": 9, "b_den": 10}]
    out = good_why(ratio_payload(rows))
    assert all(not math.isnan(r["total_effect_pp"]) for r in out["rows"])
    assert abs(sum(r["total_effect_pp"] for r in out["rows"]) - out["delta_pp"]) < 2e-2


def test_why_ratio_zero_total_denominator_fails_with_clear_message():
    for rows in ([{"key": "a", "a_num": 0, "a_den": 0, "b_num": 1, "b_den": 2}],
                 [{"key": "a", "a_num": 1, "a_den": 2, "b_num": 0, "b_den": 0}], []):
        result, out = why(ratio_payload(rows))
        assert result.returncode != 0 and out is None
        assert "zero denominator" in result.stderr, result.stderr


def test_why_huge_and_nan_values_do_not_crash():
    for rows in ([{"key": "a", "a": 1e308, "b": -1e308}, {"key": "b", "a": 1e308, "b": 1e308}],
                 [{"key": "a", "a": float("nan"), "b": 1}, {"key": "b", "a": 2, "b": 1}],
                 [{"key": "a", "a": 10 ** 30, "b": 1}]):
        result, _ = why(additive_payload(rows))
        assert result.returncode == 0 and "Traceback" not in result.stderr, result.stderr


def test_why_malformed_input_fails_nonzero():
    for payload in ("not json", "[]", "{}", json.dumps({"kind": "additive", "rows": [{"key": "a"}]}),
                    json.dumps({"kind": "ratio", "rows": [{"key": "a", "a_num": 1}]})):
        with tempfile.TemporaryDirectory() as tmp:
            result = run([WHY, write(tmp, "in.json", payload)])
        assert result.returncode != 0 and result.stderr.strip(), payload


def test_why_unknown_kind_is_rejected():
    payload = {**additive_payload([{"key": "a", "a": 5, "b": 1}]), "kind": "ratoi"}
    result, _ = why(payload)
    assert result.returncode != 0, "unknown kind accepted"


# ---------------------------------------------------------------- check

def check(cases, results, today="2031-06-01", extra=None):
    with tempfile.TemporaryDirectory() as tmp:
        golden = write(tmp, "g.json", extra if extra is not None else {"cases": cases})
        res = write(tmp, "r.json", results)
        return run([CHECK, golden, res, "--today", today])


def statuses(result):
    return {line.split()[1]: line.split()[0] for line in result.stdout.splitlines() if line[:1].isupper()}


def test_check_empty_cases_and_empty_results():
    result = check([], {})
    assert result.returncode == 0 and "0 ok, 0 drift, 0 missing, 0 expired" in result.stdout


def test_check_null_result_is_missing_and_fails():
    result = check([{"id": "a", "expected": 5}], {"a": None})
    assert result.returncode == 1 and statuses(result) == {"a": "MISSING"}
    result = check([{"id": "a", "expected": 5}], {})
    assert result.returncode == 1 and statuses(result) == {"a": "MISSING"}


def test_check_tolerance_zero_means_exact():
    cases = [{"id": "exact", "expected": 100, "tolerance_pct": 0}, {"id": "off", "expected": 100, "tolerance_pct": 0},
             {"id": "default", "expected": 100}]
    result = check(cases, {"exact": 100, "off": 100.000001, "default": 100})
    assert statuses(result) == {"exact": "OK", "off": "DRIFT", "default": "OK"} and result.returncode == 1


def test_check_value_exactly_at_tolerance_is_ok():
    result = check([{"id": "edge", "expected": 100, "tolerance_pct": 7}], {"edge": 107})
    assert statuses(result) == {"edge": "OK"}, result.stdout


def test_check_expected_zero():
    cases = [{"id": "z", "expected": 0, "tolerance_pct": 5}, {"id": "nz", "expected": 0, "tolerance_pct": 5},
             {"id": "huge_tol", "expected": 0, "tolerance_pct": 1e9}]
    result = check(cases, {"z": 0, "nz": 3, "huge_tol": 3})
    assert statuses(result) == {"z": "OK", "nz": "DRIFT", "huge_tol": "DRIFT"}
    assert "Traceback" not in result.stderr


def test_check_negative_expected_uses_absolute_gap():
    cases = [{"id": "n", "expected": -100, "tolerance_pct": 10}, {"id": "m", "expected": -100, "tolerance_pct": 10}]
    assert statuses(check(cases, {"n": -105, "m": -120})) == {"n": "OK", "m": "DRIFT"}


def test_check_nan_and_infinity_results_are_never_ok():
    cases = [{"id": "n", "expected": 10, "tolerance_pct": 50}, {"id": "i", "expected": 10, "tolerance_pct": 50},
             {"id": "j", "expected": 10, "tolerance_pct": 50}]
    with tempfile.TemporaryDirectory() as tmp:
        golden = write(tmp, "g.json", {"cases": cases})
        res = write(tmp, "r.json", '{"n": NaN, "i": Infinity, "j": -Infinity}')
        result = run([CHECK, golden, res, "--today", "2031-06-01"])
    assert statuses(result) == {"n": "DRIFT", "i": "DRIFT", "j": "DRIFT"} and result.returncode == 1


def test_check_expiry_window_boundary():
    def case(days_ago, window=28):
        return {"id": "c", "expected": 5, "date": iso(-days_ago, date(2031, 6, 1)), "window_days": window}
    assert statuses(check([case(28)], {"c": 5})) == {"c": "OK"}              # date + window == today: still inside
    assert statuses(check([case(29)], {"c": 5})) == {"c": "EXPIRED"}         # one day past the edge
    assert statuses(check([case(29)], {})) == {"c": "EXPIRED"}               # expired beats missing
    assert check([case(29)], {}).returncode == 0                              # an expired case does not fail the run
    assert statuses(check([case(-5)], {"c": 5})) == {"c": "OK"}              # a future case date never expires
    # a case without both date and window never expires
    assert statuses(check([{"id": "c", "expected": 5, "date": "2031-01-01"}], {"c": 5})) == {"c": "OK"}


def test_check_results_for_unknown_ids_are_ignored():
    result = check([{"id": "a", "expected": 5}], {"a": 5, "ghost": 1, "other": None})
    assert result.returncode == 0 and statuses(result) == {"a": "OK"}


def test_check_malformed_golden_fails_nonzero_with_a_message():
    bad_goldens = ["not json", "", "[]", "{}", '{"cases": [{"expected": 5}]}', '{"cases": [{"id": "a"}]}',
                   '{"cases": [{"id": "a", "expected": null}]}', '{"cases": 7}',
                   '{"cases": [{"id": "a", "expected": 5, "date": "bad", "window_days": 3}]}']
    for text in bad_goldens:
        result = check(None, {"a": 5}, extra=text)
        assert result.returncode != 0 and result.stderr.strip(), text
        assert "ok" not in result.stdout.lower() or text == "", text


def test_check_malformed_golden_is_distinguishable_from_drift():
    result = check(None, {"a": 5}, extra="not json")
    assert result.returncode not in (0, 1) and "Traceback" not in result.stderr, (result.returncode, result.stderr)


def test_check_malformed_results_fails_nonzero():
    with tempfile.TemporaryDirectory() as tmp:
        golden = write(tmp, "g.json", {"cases": [{"id": "a", "expected": 5}]})
        for text in ("oops", "[]", '{"a": "5"}'):
            result = run([CHECK, golden, write(tmp, "r.json", text)])
            assert result.returncode != 0, text


def test_check_unicode_labels_and_duplicate_ids():
    cases = [{"id": "d", "label": "café 中文", "expected": 5}, {"id": "d", "expected": 6}]
    result = check(cases, {"d": 5})
    assert result.returncode == 1 and "1 ok, 1 drift" in result.stdout


# ---------------------------------------------------------------- build_report

def report(**overrides):
    base = {"title": "t", "subtitle": "s", "kpis": [], "notes": [],
            "charts": [{"type": "line", "title": "c", "unit": "", "labels": ["a", "b"], "series": [{"name": "x", "data": [1, 2]}]}]}
    return {**base, **overrides}


def build(payload, env=None, script=BUILD):
    with tempfile.TemporaryDirectory() as tmp:
        src = write(tmp, "r.json", payload)
        out = Path(tmp) / "out.html"
        result = run([script, src, out], env=env)
        return result, (out.read_text(encoding="utf-8") if out.exists() else None)


def good_build(payload, env=None):
    result, text = build(payload, env)
    assert result.returncode == 0 and text, result.stderr
    return text


def embedded_block(text):
    match = re.search(r"const REPORT = (\{.*?\n\});", text, flags=re.S)
    assert match, "REPORT block not found"
    return match.group(1)


class TagCollector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)


def tags_of(text):
    parser = TagCollector()
    parser.feed(text)
    return parser.tags


HOSTILE = ["</script><img src=x onerror=alert(1)>", "</SCRIPT >", "<!-- <script>", "\"; alert(1); //",
           "'\\\"`${1}", "<img src=x onerror=alert(1)>", "café 中文    \U0001F600", "a\nb\r\n};\n"]


def hostile_report(text):
    return report(title=text, subtitle=text, notes=[text], alerts=[{"level": "bad", "text": text}],
                  kpis=[{"label": text, "value": 1, "note": text, "hint": text, "unit": text}],
                  charts=[{"type": "bar", "title": text, "unit": text, "tab": text, "labels": [text],
                           "series": [{"name": text, "data": [1]}]}])


def test_build_report_baseline_tag_count():
    plain = tags_of(good_build(report()))
    assert plain.count("script") == 2  # the chart library and the data script


def test_build_report_data_roundtrips_hostile_strings():
    for text in HOSTILE:
        payload = hostile_report(text)
        block = embedded_block(good_build(payload))
        assert json.loads(block)["title"] == text, text
        assert json.loads(block)["alerts"][0]["text"] == text, text


def test_build_report_script_breakout_is_impossible():
    baseline = tags_of(good_build(report()))
    for text in HOSTILE:
        out = good_build(hostile_report(text))
        block = embedded_block(out)
        assert "</script" not in block.lower(), f"unescaped script close in data block for {text!r}"
        assert "<!--" not in block, f"unescaped comment opener for {text!r}"
        tags = tags_of(out)
        assert tags.count("script") == baseline.count("script"), f"extra script element for {text!r}"
        assert "img" not in tags, f"injected img element for {text!r}"


def test_build_report_hostile_text_stays_inside_one_script_element_when_no_breakout_sequence():
    out = good_build(hostile_report("<img src=x onerror=alert(1)> \"quoted\" 'single' 中文"))
    assert "img" not in tags_of(out)


def test_build_report_backslash_and_dollar_sequences_are_not_read_as_regex_escapes():
    text = "a\\1 b\\g<0> \\n \\\\ $1 ${x}"
    block = embedded_block(good_build(report(title=text)))
    assert json.loads(block)["title"] == text


def test_build_report_unknown_metric_key_is_rejected():
    for key in ("nope", "GGR", "", "ggr ", "__proto__"):
        for where in ("kpis", "charts"):
            payload = report()
            item = {"label": "k", "value": 1, "metric": key} if where == "kpis" else {**payload["charts"][0], "metric": key}
            payload[where] = payload[where] + [item]
            result, text = build(payload)
            assert result.returncode != 0 and text is None, (key, where)
            assert "unknown metric key" in result.stderr, result.stderr


def test_build_report_registry_status_wins_over_user_status():
    payload = report(kpis=[{"label": "k", "value": 1, "metric": "ggr", "status": "standard"},
                           {"label": "n", "value": 1, "metric": "ngr"},
                           {"label": "d", "value": 1, "metric": "deposits"}])
    kpis = json.loads(embedded_block(good_build(payload)))["kpis"]
    assert [k["status"] for k in kpis] == ["candidate", "not_defined", "standard"]


def test_build_report_status_override_file():
    with tempfile.TemporaryDirectory() as tmp:
        override = write(tmp, "o.json", {"ggr": "approved", "brand_new_metric": "standard"})
        env = {"RENTA_METRICS_STATUS": str(override), "PATH": "/usr/bin:/bin"}
        payload = report(kpis=[{"label": "k", "value": 1, "metric": "ggr"}, {"label": "b", "value": 1, "metric": "brand_new_metric"}])
        kpis = json.loads(embedded_block(good_build(payload, env)))["kpis"]
        assert [k["status"] for k in kpis] == ["approved", "standard"]
        # a missing override file must not weaken the default badge
        env = {"RENTA_METRICS_STATUS": str(Path(tmp) / "missing.json"), "PATH": "/usr/bin:/bin"}
        only_ggr = report(kpis=[{"label": "k", "value": 1, "metric": "ggr"}])
        kpis = json.loads(embedded_block(good_build(only_ggr, env)))["kpis"]
        assert kpis[0]["status"] == "candidate"


def test_build_report_malformed_override_file_fails_loudly():
    with tempfile.TemporaryDirectory() as tmp:
        env = {"RENTA_METRICS_STATUS": str(write(tmp, "o.json", "{oops")), "PATH": "/usr/bin:/bin"}
        result, text = build(report(), env)
        assert result.returncode != 0 and text is None


def test_build_report_missing_registry_does_not_fail_open():
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "renta-visuals"
        shutil.copytree(VISUALS, copy, ignore=shutil.ignore_patterns("__pycache__"))
        (copy / "references" / "metrics_registry.json").unlink()
        payload = report(kpis=[{"label": "k", "value": 1, "metric": "nope"}])
        result, text = build(payload, script=copy / "scripts" / "build_report.py")
        assert result.returncode != 0 and text is None, "unknown metric accepted while the registry is missing"


def test_build_report_required_fields_and_chart_validation():
    for field in ("title", "subtitle", "kpis", "charts", "notes"):
        payload = report()
        del payload[field]
        result, text = build(payload)
        assert result.returncode != 0 and text is None and f"missing field: {field}" in result.stderr, field
    chart = report()["charts"][0]
    for bad in ({**chart, "type": "radar"}, {**chart, "type": None}):
        result, text = build(report(charts=[bad]))
        assert result.returncode != 0 and "bad chart type" in result.stderr
    for alert in ({"level": "fatal", "text": "x"}, {"level": "warn", "text": ""}, {"level": "warn"}):
        result, text = build(report(alerts=[alert]))
        assert result.returncode != 0 and "bad alert" in result.stderr, alert


def test_build_report_series_length_must_match_labels():
    chart = report()["charts"][0]
    for series in ([{"name": "x", "data": [1]}], [{"name": "x", "data": [1, 2, 3]}],
                   [{"name": "ok", "data": [1, 2]}, {"name": "short", "data": []}]):
        result, text = build(report(charts=[{**chart, "series": series}]))
        assert result.returncode != 0 and text is None and "values vs" in result.stderr, series


def test_build_report_empty_collections_are_fine():
    for payload in (report(charts=[]), report(kpis=[], notes=[], charts=[]), report(alerts=[]),
                    report(charts=[{"type": "bar", "title": "e", "unit": "", "labels": [], "series": []}]),
                    report(charts=[{"type": "doughnut", "title": "e", "unit": "", "labels": [], "series": [{"name": "s", "data": []}]}])):
        out = good_build(payload)
        assert json.loads(embedded_block(out))["title"] == "t"


def test_build_report_huge_arrays_render_in_reasonable_time():
    count = 2 * 10 ** 4
    labels = [iso(i % 3000) + f"#{i}" for i in range(count)]
    chart = {"type": "line", "title": "big", "unit": "", "labels": labels,
             "series": [{"name": f"s{n}", "data": list(range(count))} for n in range(3)]}
    started = time.monotonic()
    out = good_build(report(charts=[chart], notes=["n"] * (2 * 10 ** 3)))
    assert time.monotonic() - started < 20
    parsed = json.loads(embedded_block(out))
    assert len(parsed["charts"][0]["labels"]) == count and len(parsed["notes"]) == 2 * 10 ** 3


def test_build_report_nan_numbers_are_rejected_or_nulled():
    nan, inf = float("nan"), float("inf")
    payload = report(kpis=[{"label": "k", "value": nan}],
                     charts=[{"type": "line", "title": "c", "unit": "", "labels": ["a", "b"],
                              "series": [{"name": "x", "data": [nan, inf]}]}])
    result, text = build(payload)
    if result.returncode != 0:
        return  # rejected: acceptable
    block = embedded_block(text)
    assert not re.search(r"\b(NaN|-?Infinity)\b", block), "bare NaN/Infinity in the data block"


def test_build_report_cli_usage_and_missing_input():
    assert run([BUILD, "only-one-arg", "b", "c"]).returncode != 0
    with tempfile.TemporaryDirectory() as tmp:
        result = run([BUILD, Path(tmp) / "absent.json", Path(tmp) / "o.html"])
        assert result.returncode != 0 and not (Path(tmp) / "o.html").exists()
        result = run([BUILD, write(tmp, "bad.json", "{oops"), Path(tmp) / "o.html"])
        assert result.returncode != 0 and not (Path(tmp) / "o.html").exists()


# ---------------------------------------------------------------- use cases

def test_usecase_daily_brief_flow():
    """35 synthetic days with one injected spike -> anomalies.py -> build_report.py -> HTML."""
    ggr = weekly(base=1000)
    ggr[-1] = 3500  # the injected spike on the last day
    deposits = weekly(base=800)
    payload = {"metrics": [metric(ggr, name="ggr", unit="USD"), metric(deposits, name="deposits", unit="USD")],
               "freshness": [{"model": "payments", "max_date": iso(30)}], "as_of": iso(34)}
    result, out = anomalies(payload)
    assert result.returncode == 0, result.stderr
    assert [f["name"] for f in out["flags"]] == ["ggr"] and out["flags"][0]["flag"] == "high"
    assert out["stale_models"][0]["model"] == "payments" and out["stale_models"][0]["lag_days"] == 4
    by_name = {m["name"]: m for m in out["metrics"]}
    alerts = [{"level": "warn", "text": f"{f['name']} is {f['flag']}: {f['vs_baseline_pct']}% vs the same weekday median"} for f in out["flags"]]
    alerts += [{"level": "bad", "text": f"STALE: {s['model']} is {s['lag_days']} days behind"} for s in out["stale_models"]]
    brief = report(
        title="Daily brief", subtitle=f"{out['as_of']} UTC", alerts=alerts,
        kpis=[{"label": "GGR", "value": by_name["ggr"]["value"], "metric": "ggr", "delta_pct": by_name["ggr"]["vs_last_week_pct"]},
              {"label": "Deposits", "value": by_name["deposits"]["value"], "metric": "deposits"},
              {"label": "NGR", "value": 1, "metric": "ngr"}],
        charts=[{"type": "line", "title": "GGR", "unit": "USD", "metric": "ggr", "labels": metric(ggr)["dates"],
                 "series": [{"name": "ggr", "data": ggr}]}])
    html_out = good_build(brief)
    parsed = json.loads(embedded_block(html_out))
    assert any("ggr is high" in a["text"] for a in parsed["alerts"]) and any("STALE: payments" in a["text"] for a in parsed["alerts"])
    kpi_status = {k["label"]: k["status"] for k in parsed["kpis"]}
    assert kpi_status == {"GGR": "candidate", "Deposits": "standard", "NGR": "not_defined"}
    assert parsed["charts"][0]["status"] == "candidate" and len(parsed["charts"][0]["series"][0]["data"]) == 35
    assert tags_of(html_out).count("script") == 2


def test_usecase_quiet_day_has_no_alerts():
    result, out = anomalies({"metrics": [metric(weekly(base=1000), name="ggr")], "as_of": iso(34)})
    assert out["flags"] == [] and out["stale_models"] == []


def test_usecase_why_decomposition_flow():
    """Six regions, one injected jump -> why.py names it first -> the report carries the ranking."""
    regions = ["north", "south", "east", "west", "centre", "coast"]
    rng = random.Random(2)
    rows = [{"key": r, "a": 1000 + rng.randint(-20, 20), "b": 1000} for r in regions]
    rows[3]["a"] = 1900  # injected contributor: west
    out = good_why(additive_payload(rows))
    assert out["rows"][0]["key"] == "west" and out["rows"][0]["delta"] == 900
    assert abs(sum(r["delta"] for r in out["rows"]) - out["delta"]) < 1e-9
    assert out["rows"][0]["share_of_change_pct"] > 80
    chart = {"type": "bar", "title": "Change by region", "unit": "USD", "horizontal": True,
             "labels": [r["key"] for r in out["rows"]], "series": [{"name": "delta", "data": [r["delta"] for r in out["rows"]]}]}
    parsed = json.loads(embedded_block(good_build(report(charts=[chart], notes=["west leads the change"]))))
    assert parsed["charts"][0]["labels"][0] == "west"


def test_usecase_why_ratio_flow_names_the_injected_segment():
    rows = [{"key": k, "a_num": 50, "a_den": 100, "b_num": 50, "b_den": 100} for k in ("alpha", "beta", "gamma")]
    rows[1] = {"key": "beta", "a_num": 20, "a_den": 100, "b_num": 50, "b_den": 100}  # beta conversion collapsed
    out = good_why(ratio_payload(rows))
    assert out["rows"][0]["key"] == "beta" and out["delta_pp"] < 0
    assert out["rows"][0]["rate_effect_pp"] < 0


# ---------------------------------------------------------------- runner

if __name__ == "__main__":
    tests = [fn for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    passed = known = failed = 0
    for fn in tests:
        severity = getattr(fn, "known_bug", None)
        try:
            fn()
        except Exception as error:  # a crash inside a test is a failure of that test, not of the runner
            if severity:
                known += 1
                print(f"KNOWN BUG [{severity}]  {fn.__name__}: {type(error).__name__} {str(error)[:100]}")
            else:
                failed += 1
                print(f"FAIL  {fn.__name__}: {type(error).__name__} {str(error)[:300]}")
            continue
        passed += 1
        print(f"ok  {fn.__name__}" + ("  (FIXED? known-bug test now passes, remove the marker)" if severity else ""))
    print(f"{len(tests)} tests: {passed} passed, {known} known bugs, {failed} failed")
    sys.exit(1 if failed else 0)
