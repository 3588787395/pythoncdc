#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synthetic checks for fuzz_driver, minimize and canary leak scanning."""

from __future__ import annotations

import json
import os
import shutil
import tempfile

import canary_runner as cr
import fuzz_driver as fd
import minimize as mn


def main():
    root = tempfile.mkdtemp(prefix="fuzz_selftest_")
    try:
        first = fd.generate_cases(7, 9)
        second = fd.generate_cases(7, 9)
        good = fd.evaluate_source("def main():\n    return 1\n", "good", os.path.join(root, "good"),
                                  timeout=20.0)
        bad_lines = ["def f():", "    x = 1", "    BAD = 2", "    return x", ""]
        reduced, tests, exhausted = mn.ddmin(
            bad_lines, lambda source: "BAD" in source and "def f" in source, 40, 1e12)
        public = os.path.join(root, "public")
        private = os.path.join(root, "private")
        os.makedirs(public, exist_ok=True)
        os.makedirs(private, exist_ok=True)
        with open(os.path.join(public, "leak.txt"), "w", encoding="utf-8") as fh:
            fh.write("contains SECRET_CANARY_FEATURE_123 here\n")
        with open(os.path.join(private, "canary.json"), "w", encoding="utf-8") as fh:
            json.dump({"canary_id": "C1", "category": "rare_syntax",
                       "source": "def main():\n    return 1\n",
                       "features": ["SECRET_CANARY_FEATURE_123"]}, fh)
        canaries = cr.load_canaries(private)
        hit = cr.scan_leaks(canaries, [public])
        excluded = cr.scan_leaks(canaries, [private], exclude=private)
        checks = {
            "generator_deterministic": [c["source"] for c in first] == [c["source"] for c in second],
            "generator_9_cases": len(first) == 9,
            "generator_3_families": len({c["family"] for c in first}) == 3,
            "generator_no_placeholder": all("@N@" not in c["source"] for c in first),
            "generator_sources_compile": all(
                compile(c["source"], c["case_id"], "exec") is not None for c in first),
            "good_source_equal": good.get("status") == "EQUAL",
            "ddmin_keeps_failure": "BAD" in "\n".join(reduced) and len(reduced) < len(bad_lines),
            "ddmin_tests": tests > 0 and not exhausted,
            "canary_loader": len(canaries) == 1,
            "leak_detected": len(hit) == 1,
            "leak_excluded": len(excluded) == 0,
        }
        payload = {"tool": "fuzz_selftest", "checks": checks, "passed": all(checks.values()),
                   "good_status": good.get("status"), "reduced_lines": len(reduced),
                   "ddmin_tests": tests}
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 0 if payload["passed"] else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
