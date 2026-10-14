#!/usr/bin/env python3
"""Render a Renta report into the dashboard template.

Usage: python3 -I build_report.py report.json out.html
       python3 -I build_report.py            (self-check)
report.json: {title, subtitle, kpis[], charts[], notes[]} (see renta-visuals/SKILL.md).
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "assets" / "dashboard.html"
REGISTRY = ROOT / "references" / "metrics_registry.json"
CHART_TYPES = {"line", "bar", "doughnut"}
ALERT_LEVELS = {"info", "warn", "bad"}


def load_statuses():
    """Metric key -> status: registry defaults, then the optional override file named by RENTA_METRICS_STATUS."""
    if not REGISTRY.is_file():
        raise ValueError(f"metrics registry not found: {REGISTRY}")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["metrics"]
    statuses = {key: value["status"] for key, value in registry.items()}
    override = os.environ.get("RENTA_METRICS_STATUS")
    if override and Path(override).is_file():
        statuses.update(json.loads(Path(override).read_text(encoding="utf-8")))
    return statuses


def apply_statuses(report):
    """Items with a "metric" key get their status from the registry (typos fail loudly)."""
    statuses = load_statuses()
    for item in report["kpis"] + report["charts"]:
        key = item.get("metric")
        if key is None:
            continue
        if key not in statuses:
            raise ValueError(f"unknown metric key: {key}")
        item["status"] = statuses[key]
    return report


def validate(report):
    for key in ("title", "subtitle", "kpis", "charts", "notes"):
        if key not in report:
            raise ValueError(f"missing field: {key}")
    for alert in report.get("alerts", []):
        if alert.get("level", "info") not in ALERT_LEVELS or not alert.get("text"):
            raise ValueError(f"bad alert: {alert}")
    for chart in report["charts"]:
        if chart.get("type") not in CHART_TYPES:
            raise ValueError(f"bad chart type: {chart.get('type')}")
        for series in chart["series"]:
            if len(series["data"]) != len(chart["labels"]):
                raise ValueError(f"'{chart['title']}': {len(series['data'])} values vs {len(chart['labels'])} labels")


def render(report):
    validate(report)
    apply_statuses(report)
    html = TEMPLATE.read_text(encoding="utf-8")
    # "<" and the JS line separators are escaped so no text can close the script block or break the string
    data = json.dumps(report, ensure_ascii=False, indent=1, allow_nan=False)
    data = data.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    block = "const REPORT = " + data + ";"
    # function replacement, so backslashes in the data are not read as escapes
    out, count = re.subn(r"const REPORT = \{.*?\n\};", lambda _: block, html, count=1, flags=re.S)
    if count != 1:
        raise ValueError("REPORT object not found in the template")
    return out


def demo():
    sample = {"title": "t", "subtitle": "s", "kpis": [], "notes": [],
              "charts": [{"type": "line", "title": "c", "unit": "", "labels": ["a", "b"], "series": [{"name": "x", "data": [1, 2]}]}]}
    assert '"title": "t"' in render(sample)
    labelled = {**sample, "kpis": [{"label": "k", "value": 1, "metric": "ggr"}]}
    assert '"status": "candidate"' in render(labelled)
    for bad in ({**sample, "kpis": [{"label": "k", "value": 1, "metric": "nope"}]},
                {**sample, "alerts": [{"level": "x", "text": "t"}]}):
        try:
            render(bad)
        except ValueError:
            continue
        raise AssertionError("bad report not caught")
    sample["charts"][0]["series"][0]["data"] = [1]
    try:
        render(sample)
    except ValueError:
        return
    raise AssertionError("length mismatch not caught")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        demo()
        print("self-check ok")
    elif len(sys.argv) == 3:
        try:
            html = render(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
        except (ValueError, KeyError, TypeError, OSError) as error:
            print(f"error: {error!r}", file=sys.stderr)
            sys.exit(2)
        Path(sys.argv[2]).write_text(html, encoding="utf-8")
        print(sys.argv[2])
    else:
        sys.exit(__doc__)
