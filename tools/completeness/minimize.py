#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Line-level ddmin for fuzz.py failures (Task 9.5).

The predicate is the same compile -> decompile -> semantic_diff pipeline.  A
candidate is accepted only if it preserves the original failure status, so
ddmin cannot "minimize" a semantic diff down to an unrelated compile error.
Original source and seed are always copied into the output directory.

CLI:
    python -X utf8 tools/completeness/minimize.py \
        --input logs/fuzz_report.jsonl --out logs/minimized/ --limit 8
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fuzz_driver as fd

TOOL_VERSION = "1.0.0"
FAILURE_STATUSES = fd.FAILURE_STATUSES


def load_jsonl(path: str) -> list[dict]:
    out = []
    with open(path, "r", encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _test_source(source: str, record: dict, timeout: float, decompiler: str) -> dict:
    workdir = tempfile.mkdtemp(prefix="minimize_")
    try:
        return fd.evaluate_source(
            source, record.get("case_id", "candidate"), workdir,
            entrypoint=record.get("entrypoint") or "main",
            args=record.get("args") or [], kwargs=record.get("kwargs") or {},
            seed=int(record.get("seed") or 0), decompiler=decompiler, timeout=timeout)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def ddmin(lines: list[str], predicate, max_tests: int, deadline: float):
    tests = 0
    exhausted = False
    n = 2
    lines = list(lines)
    while len(lines) >= 2:
        if tests >= max_tests or time.monotonic() >= deadline:
            exhausted = True
            break
        chunk = int(math.ceil(len(lines) / float(n)))
        reduced = False
        for start in range(0, len(lines), chunk):
            if tests >= max_tests or time.monotonic() >= deadline:
                exhausted = True
                break
            candidate = lines[:start] + lines[start + chunk:]
            if not candidate:
                continue
            tests += 1
            if predicate("\n".join(candidate).rstrip() + "\n"):
                lines = candidate
                n = max(2, n - 1)
                reduced = True
                break
        if reduced:
            continue
        if n >= len(lines):
            break
        n = min(len(lines), n * 2)
    return lines, tests, exhausted


def minimize_record(record: dict, out_dir: str, *, timeout: float, decompiler: str,
                    max_tests: int, deadline: float) -> dict:
    case_id = record.get("case_id", "case")
    status = record.get("status")
    source_path = record.get("source_path") or ""
    if status not in FAILURE_STATUSES:
        return {"case_id": case_id, "status": "SKIPPED", "reason": "not_a_failure"}
    if not source_path or not os.path.isfile(source_path):
        return {"case_id": case_id, "status": "SKIPPED", "reason": "source_missing"}
    with open(source_path, "r", encoding="utf-8-sig", errors="replace") as fh:
        original = fh.read()
    original_copy = os.path.join(out_dir, case_id + ".original.py")
    with open(original_copy, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(original)
    lines = original.splitlines()
    original_dims = {d.get("dimension") for d in (record.get("diffs") or []) if d.get("dimension")}

    def predicate(candidate: str) -> bool:
        try:
            result = _test_source(candidate, record, timeout, decompiler)
        except BaseException:
            return False
        if result.get("status") != status:
            return False
        if status == "DIFFERENT":
            dims = {d.get("dimension") for d in (result.get("diffs") or []) if d.get("dimension")}
            if dims != original_dims:
                return False
        return True

    if not predicate(original):
        return {"case_id": case_id, "status": "SKIPPED", "reason": "original_not_reproducible",
                "original_path": original_copy}
    reduced, tests, exhausted = ddmin(lines, predicate, max_tests, deadline)
    minimized = "\n".join(reduced).rstrip() + "\n"
    final = _test_source(minimized, record, timeout, decompiler)
    tests += 1
    if final.get("status") != status:
        reduced = lines
        minimized = original
        final = _test_source(minimized, record, timeout, decompiler)
        tests += 1
    minimized_path = os.path.join(out_dir, case_id + ".min.py")
    with open(minimized_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(minimized)
    final_dims = sorted({d.get("dimension") for d in (final.get("diffs") or []) if d.get("dimension")})
    return {
        "case_id": case_id, "status": status, "minimized_status": final.get("status"),
        "minimized_differences": final_dims,
        "original_lines": len(lines), "minimized_lines": len(reduced),
        "removed_lines": len(lines) - len(reduced),
        "tests": tests, "budget_exhausted": exhausted,
        "seed": record.get("seed"), "entrypoint": record.get("entrypoint"),
        "source_sha256": record.get("source_sha256"),
        "minimized_sha256": fd.sha_text(minimized),
        "first_diff_dimension": (record.get("diffs") or [{}])[0].get("dimension"),
        "original_path": original_copy, "minimized_path": minimized_path,
        "family": record.get("family"), "template": record.get("template"),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="minimize fuzz failures")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--decompiler", default=fd.PYCDC)
    parser.add_argument("--max-tests", type=int, default=120)
    parser.add_argument("--seconds", type=float, default=300.0)
    parser.add_argument("--json", default="")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    records = load_jsonl(args.input)
    failures = [r for r in records if r.get("status") in FAILURE_STATUSES]
    if args.limit > 0:
        failures = failures[:args.limit]
    deadline = time.monotonic() + max(1.0, args.seconds)
    results = []
    for record in failures:
        result = minimize_record(record, args.out, timeout=args.timeout,
                                 decompiler=args.decompiler, max_tests=args.max_tests,
                                 deadline=deadline)
        results.append(result)
        print("[minimize] %-32s %s lines=%s/%s tests=%s"
              % (result.get("case_id"), result.get("status"),
                 result.get("minimized_lines"), result.get("original_lines"),
                 result.get("tests")))
    payload = {
        "tool": "minimize", "version": TOOL_VERSION,
        "input": args.input, "total_failures": len(failures),
        "minimized": sum(1 for r in results if r.get("minimized_path")),
        "results": results,
    }
    out_json = args.json or os.path.join(args.out, "minimized.json")
    with open(out_json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[minimize] total=%d minimized=%d report=%s"
          % (len(failures), payload["minimized"], out_json))
    return 0 if payload["minimized"] == len(failures) else 1


if __name__ == "__main__":
    sys.exit(main())
