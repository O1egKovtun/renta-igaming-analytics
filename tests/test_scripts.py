#!/usr/bin/env python3
"""Runs every script self-check and the report builder. Usage: python3 tests/test_scripts.py"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = [sys.executable, "-I"]


def run(args, stdin=None, env=None):
    return subprocess.run(PY + [str(a) for a in args], input=stdin, capture_output=True, text=True, env=env)


def test_selftests():
    for name in ("anomalies", "why", "check"):
        result = run([ROOT / "scripts" / f"{name}.py", "selftest"])
        assert result.returncode == 0, f"{name}: {result.stderr}"
    assert run([ROOT / "skills" / "renta-visuals" / "scripts" / "build_report.py"]).returncode == 0


def test_report_badges_and_alerts():
    with tempfile.TemporaryDirectory() as tmp:
        report = {"title": "t", "subtitle": "s", "notes": [], "alerts": [{"level": "warn", "text": "x"}],
                  "kpis": [{"label": "GGR", "value": 1, "metric": "ggr"}],
                  "charts": [{"type": "bar", "title": "c", "unit": "", "labels": ["a"], "series": [{"name": "s", "data": [1]}], "tab": "T"}]}
        src, out = Path(tmp) / "r.json", Path(tmp) / "r.html"
        src.write_text(json.dumps(report), encoding="utf-8")
        result = run([ROOT / "skills" / "renta-visuals" / "scripts" / "build_report.py", src, out])
        assert result.returncode == 0, result.stderr
        assert '"status": "candidate"' in out.read_text(encoding="utf-8")


if __name__ == "__main__":
    tests = [fn for name, fn in sorted(globals().items()) if name.startswith("test_")]
    for fn in tests:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"{len(tests)} passed")
