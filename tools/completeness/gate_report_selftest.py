#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synthetic checks that gate_report does not turn missing/failing evidence into PASS."""

from __future__ import annotations

import json
import os
import tempfile

import gate_report as gr


def write(root: str, name: str, payload) -> str:
    path = os.path.join(root, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        if isinstance(payload, str):
            fh.write(payload)
        else:
            json.dump(payload, fh, ensure_ascii=False)
    return path


def main() -> int:
    root = tempfile.mkdtemp(prefix="gate_selftest_")
    try:
        complete_cov = {"totals": {"J_total": 10, "covered_5tuple": 10,
                                   "semantic_failures": 0, "probe_only": 0,
                                   "uncovered": 0, "coverage_pct": 100.0}}
        partial_cov = {"totals": {"J_total": 10, "covered_5tuple": 9,
                                  "semantic_failures": 0, "probe_only": 1,
                                  "uncovered": 1, "coverage_pct": 90.0}}
        mutation_ok = write(root, "mutation_ok.json",
                            {"mix": {"KILLED": 10, "MISSED": 0, "EQUIVALENT": 0,
                                     "FALSE_KILL": 0, "INCONCLUSIVE": 0, "ERROR": 0}})
        mutation_fail = write(root, "mutation_fail.json",
                              {"mix": {"KILLED": 10, "MISSED": 1, "EQUIVALENT": 0,
                                       "FALSE_KILL": 0, "INCONCLUSIVE": 0, "ERROR": 0}})
        canary_pass = write(root, "canary_pass.json",
                            {"canaries": 24, "equal": 24, "g6": "PASS",
                             "counts": {"EQUAL": 24}, "leak_hits": []})
        canary_fail = write(root, "canary_fail.json",
                            {"canaries": 24, "equal": 20, "g6": "FAIL",
                             "counts": {"EQUAL": 20, "DIFFERENT": 4}, "leak_hits": []})
        semantic_summary = write(root, "semantic.json",
                                 {"total": 51, "verdicts": {"EQUAL": 45, "DIFFERENT": 6}})
        args = type("Args", (), {
            "coverage": write(root, "cov.json", partial_cov),
            "coverage_baseline": write(root, "cov0.json", {"totals": {"J_total": 10,
                                                                      "covered_5tuple": 0}}),
            "semantic_j": write(root, "sem.json", {"records": [{
                "entry_id": "SELFTEST-FAIL", "c1": {}, "c2": {}, "c3": {},
                "c4": {"verdict": "DIFFERENT"}, "c5": {}}]}),
            "semantic_summary": semantic_summary,
            "semantic_402": "", "semantic_real": "", "mutation": mutation_ok,
            "rules": write(root, "rules.json", {"g4": "INCONCLUSIVE", "total_rules": 1,
                                                "proved": 0, "open": 1}),
            "regression": write(root, "reg.json", {
                "total": {"units_success": 6617, "units_total": 6617, "files_failure": 0},
                "small34": {"units_success": 1568, "units_total": 1568},
                "quotation": {"rc": 0, "tail": "units=153/153 success_rate=100.00%"},
                "pytest": {"summary_line": "2 failed, 282 passed, 2 xpassed in 1s"},
                "iv2": {"IMPORT_OK": True, "COMPILE_OK": True,
                        "G3_forbidden_prefix_new_defs": 0,
                        "BOM_region_ast_generator.py": "one",
                        "BOM_region_analyzer.py": "one"}}),
            "canary": canary_fail,
        })()
        report = gr.build(args)
        checks = {
            "g1_complete_pass": gr.gate_g1(complete_cov, None)["status"] == gr.PASS,
            "g1_partial_fail": gr.gate_g1(partial_cov, None)["status"] == gr.FAIL,
            "g2a_sample_diff_fail": gr.gate_g2a({"total": 51, "verdicts": {"DIFFERENT": 6}})["status"] == gr.FAIL,
            "g2a_small_clean_unestablished": gr.gate_g2a({"total": 51, "verdicts": {}})["status"] == gr.UNESTABLISHED,
            "g3_clean_pass": gr.gate_g3(mutation_ok)["status"] == gr.PASS,
            "g3_survived_fail": gr.gate_g3(mutation_fail)["status"] == gr.FAIL,
            "g4_inconclusive": gr.gate_g4(args.rules)["status"] == gr.INCONCLUSIVE,
            "g5_baseline_pass": report["gates"]["G5"]["status"] == gr.PASS,
            "g6_fail": gr.gate_g6(canary_fail)["status"] == gr.FAIL,
            "g6_missing_unestablished": gr.gate_g6(os.path.join(root, "absent.json"))["status"] == gr.UNESTABLISHED,
            "overall_blocked": report["overall"] == "BLOCKED" and "G1" in report["blockers"],
            "failure_sampled": report["audit"]["at_least_one_failure"] is True,
        }
        passed = all(checks.values())
        print(json.dumps({"tool": "gate_report_selftest", "checks": checks,
                          "passed": passed, "overall": report["overall"]},
                         ensure_ascii=False, indent=1))
        return 0 if passed else 1
    finally:
        import shutil
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
