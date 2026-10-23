#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synthetic positive/negative self-test for rule_universe + rule_manifest."""

from __future__ import annotations

import json
import os
import shutil
import tempfile

import rule_manifest as rm
import rule_universe as ru


def universe():
    return {"rules": [
        {"rule_id": "R-ONE", "anchor": "core/cfg/x.py:1", "anchors": ["core/cfg/x.py:1"],
         "file": "core/cfg/x.py", "line": 1, "kind": "isinstance_ast", "symbol": "If",
         "pattern": "isinstance(n, ast.If)"},
        {"rule_id": "R-TWO", "anchor": "core/cfg/x.py:2", "anchors": ["core/cfg/x.py:2"],
         "file": "core/cfg/x.py", "line": 2, "kind": "opcode_eq", "symbol": "JUMP",
         "pattern": "opname == 'JUMP'"},
    ]}


def manifest_from(universe_data, proved=True, status="proved"):
    manifest = rm.generate(universe_data)
    for item in manifest["rules"]:
        item["status"] = status
        item["semantic_domain"] = {"hosts": ["function-body"], "depths": ["d1"]}
        item["witnesses"] = {"positive": ["J-1"], "negative": ["J-2"]}
        item["composition"] = ["D2:J-1+J-2"]
        item["proof"] = {"proof_id": "P-" + item["rule_id"], "checker_version": "selftest",
                         "counterexample_bound": 100, "review": "selftest"}
    return manifest


def main():
    root = tempfile.mkdtemp(prefix="rule_selftest_")
    try:
        code = os.path.join(root, "core", "cfg")
        os.makedirs(code)
        with open(os.path.join(code, "sample.py"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("import ast\n")
            fh.write("def f(n, opname):\n")
            fh.write("    if isinstance(n, ast.If):\n")
            fh.write("        return 1\n")
            fh.write("    if opname == 'JUMP':\n")
            fh.write("        return 2\n")
            fh.write("    return 0\n")
        scanned = ru.build_universe(code)
        scanned2 = ru.build_universe(code)
        u = universe()
        m = manifest_from(u)
        jspace = {"entries": [{"id": "J-1"}, {"id": "J-2"}]}
        traces = {"J-1": ["R-ONE", "R-TWO"], "J-2": ["R-ONE"]}
        result = rm.check(u, m, jspace, traces)
        no_traces = rm.check(u, m, jspace, None)
        orphan_m = json.loads(json.dumps(m))
        orphan_m["rules"].append(dict(orphan_m["rules"][0], rule_id="R-ORPHAN", universe_id="R-ORPHAN"))
        orphan = rm.check(u, orphan_m, jspace, traces)
        gap_m = json.loads(json.dumps(m))
        gap_m["rules"] = gap_m["rules"][:1]
        gap = rm.check(u, gap_m, jspace, traces)
        open_m = rm.generate(u)
        open_result = rm.check(u, open_m, jspace, traces)
        empty = rm.check({"rules": []}, rm.generate({"rules": []}), jspace, traces)
        checks = {
            "universe_count_2": scanned["total_rules"] == 2,
            "universe_occurrences_2": scanned["total_occurrences"] == 2,
            "universe_deterministic": json.dumps(scanned, sort_keys=True) == json.dumps(scanned2, sort_keys=True),
            "generated_rules_2": len(rm.generate(u)["rules"]) == 2,
            "pass": result["g4"] == "PASS",
            "pass_ready_2": result["ready_proved"] == 2,
            "no_empty_cov": result["empty_cov"] == 0,
            "no_traces_inconclusive": no_traces["g4"] == "INCONCLUSIVE",
            "orphan_fail": orphan["g4"] == "FAIL" and len(orphan["orphan_rules"]) == 1,
            "unmapped_fail": gap["g4"] == "FAIL" and len(gap["unmapped_anchors"]) == 1,
            "open_fail": open_result["g4"] == "FAIL" and open_result["open"] == 2,
            "empty_inconclusive": empty["g4"] == "INCONCLUSIVE",
        }
        payload = {"tool": "rule_manifest_selftest", "checks": checks,
                   "passed": all(checks.values()), "universe": {
                       "total_rules": scanned["total_rules"],
                       "total_occurrences": scanned["total_occurrences"],
                       "counts_by_kind": scanned["counts_by_kind"]},
                   "pass_result": result, "no_traces": no_traces["reason"],
                   "orphan": orphan["g4"], "gap": gap["g4"], "open": open_result["g4"]}
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 0 if all(checks.values()) else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
