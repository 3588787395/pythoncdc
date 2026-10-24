#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-test for tools/completeness/semantic_runner.py measurement semantics.

Covers the Task-1 categories on the runner path (achieve-any-syntax-completeness):
a module-only entry (empty input_model.calls) keeps its measured verdict but is
classified probe_only/module_only and never counts as covered_5tuple; an entry
with input_model.calls passes the calls through, executes them end to end
(decompile -> semantic_diff) and can become covered_5tuple.
"""

from __future__ import annotations

import json
import os
import py_compile
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import semantic_runner as sr  # noqa: E402


def main() -> int:
    work = tempfile.mkdtemp(prefix="semantic_runner_selftest_")
    try:
        source = os.path.join(work, "probe.py")
        with open(source, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("def f(x):\n    return x + 1\n")
        pyc = os.path.join(work, "probe.pyc")
        py_compile.compile(source, cfile=pyc, doraise=True, optimize=0)
        space = {
            "tool": "semantic_runner_selftest", "seed": 0,
            "entries": [
                {"id": "WITH-CALLS", "p_j": source, "pyc": pyc, "entrypoint": "module",
                 "input_model": {"kind": "module", "calls": ["f(2)"], "seed": 0}},
                {"id": "NO-CALLS", "p_j": source, "pyc": pyc, "entrypoint": "module",
                 "input_model": {"kind": "module", "calls": [], "seed": 0}},
            ],
        }
        space_path = os.path.join(work, "space.json")
        with open(space_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(space, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        out = os.path.join(work, "out.json")
        report = os.path.join(work, "report.json")
        code = sr.main(["--space", space_path, "--out", out, "--report", report,
                        "--product-dir", os.path.join(work, "products"),
                        "--timeout", "20"])
        with open(out, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        records = {record["entry_id"]: record for record in payload["records"]}
        summary = payload.get("summary", {})
        with_calls = records.get("WITH-CALLS", {})
        no_calls = records.get("NO-CALLS", {})
        checks = [
            ("with-calls verdict EQUAL", with_calls.get("c4", {}).get("verdict") == "EQUAL"),
            ("with-calls covered_5tuple", with_calls.get("status") == "covered_5tuple"),
            ("with-calls reason empty", not with_calls.get("reason")),
            ("with-calls calls passed through",
             with_calls.get("input_model", {}).get("calls") == ["f(2)"]),
            ("no-calls verdict EQUAL", no_calls.get("c4", {}).get("verdict") == "EQUAL"),
            ("no-calls probe_only", no_calls.get("status") == "probe_only"),
            ("no-calls reason module_only", no_calls.get("reason") == "module_only"),
            ("no-calls not covered", no_calls.get("status") != "covered_5tuple"),
            ("summary module_only=1", summary.get("module_only") == 1),
            ("summary covered_5tuple=1", summary.get("covered_5tuple") == 1),
            ("summary total=2", summary.get("total") == 2),
        ]
        payload_out = {"tool": "semantic_runner_selftest", "runner_exit_code": code,
                       "checks": [{"name": name, "ok": bool(ok)} for name, ok in checks],
                       "passed": sum(1 for _, ok in checks if ok), "total": len(checks)}
        print(json.dumps(payload_out, ensure_ascii=False, indent=1))
        return 0 if all(ok for _, ok in checks) else 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
