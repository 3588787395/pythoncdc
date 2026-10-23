#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-test for tools/completeness/mutation_test.py."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

import mutation_test as mt


def write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main() -> int:
    root = tempfile.mkdtemp(prefix="mutation_test_selftest_")
    try:
        subject = os.path.join(root, "subject.py")
        write(subject, """def mix(a, b):
    if a > b:
        return a - b
    return a + b


def unused(a, b):
    return a * b
""")
        case = {
            "case_id": "selftest-mix",
            "original": {"source": subject},
            "entrypoint": "function:mix",
            "calls": [{"args": [5, 3]}, {"args": [2, 4]}, {"args": [2, 2]}],
            "_base": root,
        }
        report = mt.run_mutations(case, subject, max_mutants=50)
        summary = report.get("summary", {})
        checks = {
            "baseline_equal": report.get("baseline", {}).get("status") == "EQUAL",
            "complete": report.get("status") == "COMPLETE",
            "has_kills": summary.get("KILLED", 0) >= 5,
            "has_missed": summary.get("MISSED", 0) >= 1,
            "no_false_kill": summary.get("FALSE_KILL", 0) == 0,
        }

        eq_subject = os.path.join(root, "equivalent.py")
        write(eq_subject, "def f(x):\n    return x * 1\n")
        eq_case = {
            "case_id": "selftest-equivalent",
            "original": {"source": eq_subject},
            "entrypoint": "function:f",
            "calls": [{"args": [5]}, {"args": [-3]}],
            "_base": root,
        }
        with open(eq_subject, encoding="utf-8") as fh:
            listed = mt.generate_mutations(__import__("ast").parse(fh.read()))
        mult = [item for item in listed if item["operator"] == "binop" and item["description"].startswith("Mult")][0]
        unproven = mt.run_mutations(eq_case, eq_subject, max_mutants=50)
        unproven_mutants = {item["mutation_id"]: item for item in unproven.get("mutants", [])}
        eq = mt.run_mutations(eq_case, eq_subject, max_mutants=50,
                              equivalents={mult["mutation_id"]: {
                                  "proof": "case domain is int; x*1 == x//1 for int x"}})
        eq_summary = eq.get("summary", {})
        checks.update({
            "code_only_unproven_missed": unproven_mutants.get(mult["mutation_id"], {}).get("status") == "MISSED",
            "equivalent_complete": eq.get("status") == "COMPLETE",
            "equivalent_proven": eq_summary.get("EQUIVALENT", 0) >= 1,
            "equivalent_not_killed": eq_summary.get("FALSE_KILL", 0) == 0,
        })
        payload = {"tool": "mutation_test_selftest", "checks": checks,
                   "passed": all(checks.values()), "mix": summary,
                   "unproven": unproven.get("summary", {}),
                   "equivalent": eq_summary,
                   "mix_mutants": report.get("mutants", []),
                   "equivalent_mutants": eq.get("mutants", [])}
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 0 if all(checks.values()) else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
