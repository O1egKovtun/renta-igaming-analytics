#!/usr/bin/env python3
"""Render a Renta report into the dashboard template.

Usage: python3 -I build_report.py report.json out.html
       python3 -I build_report.py            (self-check)
report.json: {title, subtitle, kpis[], charts[], notes[]} (see renta-visuals/SKILL.md).
"""
import json
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "dashboard.html"
CHART_TYPES = {"line", "bar", "doughnut"}


def validate(report):
    for key in ("title", "subtitle", "kpis", "charts", "notes"):
        if key not in report:
            raise ValueError(f"missing field: {key}")
    for chart in report["charts"]:
        if chart.get("type") not in CHART_TYPES:
            raise ValueError(f"bad chart type: {chart.get('type')}")
        for series in chart["series"]:
            if len(series["data"]) != len(chart["labels"]):
                raise ValueError(f"'{chart['title']}': {len(series['data'])} values vs {len(chart['labels'])} labels")


def render(report):
    validate(report)
    html = TEMPLATE.read_text(encoding="utf-8")
    block = "const REPORT = " + json.dumps(report, ensure_ascii=False, indent=1) + ";"
    # function replacement, so backslashes in the data are not read as escapes
    out, count = re.subn(r"const REPORT = \{.*?\n\};", lambda _: block, html, count=1, flags=re.S)
    if count != 1:
        raise ValueError("REPORT object not found in the template")
    return out


def demo():
    sample = {"title": "t", "subtitle": "s", "kpis": [], "notes": [],
              "charts": [{"type": "line", "title": "c", "unit": "", "labels": ["a", "b"], "series": [{"name": "x", "data": [1, 2]}]}]}
    assert '"title": "t"' in render(sample)
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
        Path(sys.argv[2]).write_text(render(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))), encoding="utf-8")
        print(sys.argv[2])
    else:
        sys.exit(__doc__)
