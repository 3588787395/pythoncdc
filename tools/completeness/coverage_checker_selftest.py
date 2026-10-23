#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synthetic positive/negative self-test for C1-C5 coverage_checker."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import py_compile
import shutil
import tempfile

import coverage_checker as cc


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def record(entry_id, source, pyc, product, judge_sha, verdict="EQUAL"):
    return {
        "entry_id": entry_id,
        "c1": {"source_path": source, "sha256": sha(source), "lines": 4},
        "c2": {"pyc_path": pyc, "sha256": sha(pyc), "python_version": "3.11.7"},
        "c3": {"product_path": product, "sha256": sha(product), "command": "selftest"},
        "c4": {"verdict": verdict, "seed": 0, "exit_code": 0 if verdict == "EQUAL" else 1},
        "c5": {"source_sha256": sha(source), "pyc_sha256": sha(pyc),
               "product_sha256": sha(product), "judge_sha256": judge_sha,
               "runner_version": "selftest-1"},
    }


def main():
    root = tempfile.mkdtemp(prefix="coverage_selftest_")
    try:
        source = os.path.join(root, "probe.py")
        with open(source, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("def f(x):\n    return x + 1\n")
        pyc = os.path.join(root, "probe.pyc")
        py_compile.compile(source, cfile=pyc, doraise=True)
        product = os.path.join(root, "product.py")
        with open(product, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("def f(x):\n    return x + 1\n")
        judge = os.path.join(root, "judge.py")
        with open(judge, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# judge\n")
        judge_sha = sha(judge)
        base = {"p_j": source, "p_j_sha256": sha(source), "p_j_lines": 3,
                "pyc": pyc, "pyc_sha256": sha(pyc), "form": "If", "host": "function-body",
                "depth": "d1", "variant": "selftest", "row": "If"}

        def entry(eid, **overrides):
            item = dict(base)
            item["id"] = eid
            item.update(overrides)
            return item

        entries = [
            entry("JS-OK-001"),
            entry("JS-DIFF-001"),
            entry("JS-PROBE-001"),
            entry("JS-UNEXEC-001"),
            entry("JS-NA-001", status="n/a"),
            entry("JS-INCON-001"),
            entry("JS-EXCL-001", excluded=["language-invalid"]),
            entry("JS-NOSRC-001", p_j=os.path.join(root, "missing.py"), p_j_sha256="0" * 64),
            entry("JS-BADCHAIN-001"),
        ]
        space = {"j_schema_version": "v2", "entries": entries}
        ok = record("JS-OK-001", source, pyc, product, judge_sha)
        diff = record("JS-DIFF-001", source, pyc, product, judge_sha, verdict="DIFFERENT")
        unexec = record("JS-UNEXEC-001", source, pyc, product, judge_sha)
        unexec.pop("c4")
        del unexec["c5"]
        incon = record("JS-INCON-001", source, pyc, product, judge_sha, verdict="INCONCLUSIVE")
        bad = record("JS-BADCHAIN-001", source, pyc, product, judge_sha)
        bad["c5"]["source_sha256"] = "0" * 64
        evidence = {"records": [ok, diff, unexec, incon, bad]}
        rows, per_family = cc.check(space, {r["entry_id"]: r for r in evidence["records"]}, judge_sha)
        by_id = {row["id"]: row for row in rows}
        checks = {
            "total_9": len(rows) == 9,
            "covered_2": sum(1 for r in rows if r["status"] == "covered_5tuple") == 2,
            "green_1": sum(1 for r in rows if r["green"]) == 1,
            "semantic_failure_1": sum(1 for r in rows if r["verdict"] == "DIFFERENT") == 1,
            "probe_only": by_id["JS-PROBE-001"]["status"] == "probe_only",
            "unexecuted": by_id["JS-UNEXEC-001"]["status"] == "unexecuted",
            "n_a": by_id["JS-NA-001"]["status"] == "n/a",
            "inconclusive": by_id["JS-INCON-001"]["status"] == "inconclusive",
            "excluded": by_id["JS-EXCL-001"]["status"] == "excluded",
            "missing_source": by_id["JS-NOSRC-001"]["status"] == "uncovered",
            "bad_chain": by_id["JS-BADCHAIN-001"]["status"] == "uncovered",
            "bad_chain_reason": by_id["JS-BADCHAIN-001"]["reason"] == "c5_chain_mismatch",
        }
        space_path = os.path.join(root, "space.json")
        evidence_path = os.path.join(root, "evidence.json")
        with open(space_path, "w", encoding="utf-8") as fh:
            json.dump(space, fh)
        with open(evidence_path, "w", encoding="utf-8") as fh:
            json.dump(evidence, fh)
        with contextlib.redirect_stdout(io.StringIO()):
            gate_rc = cc.main(["--space", space_path, "--evidence", evidence_path, "--judge", judge,
                               "--json", os.path.join(root, "report.json")])
        checks["gate_fails"] = gate_rc == 1
        payload = {"tool": "coverage_checker_selftest", "checks": checks,
                   "passed": all(checks.values()),
                   "totals": {status: sum(1 for r in rows if r["status"] == status)
                              for status in ("covered_5tuple", "probe_only", "unexecuted",
                                             "n/a", "inconclusive", "excluded", "uncovered")},
                   "per_family": {k: dict(v) for k, v in per_family.items()}}
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 0 if all(checks.values()) else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
