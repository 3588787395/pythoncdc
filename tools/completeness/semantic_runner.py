#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Produce C1-C5 evidence records for a judgment-space manifest.

This is the producer that was missing in Task 9.3: it binds the source hash,
pyc hash, regenerated product hash, the semantic_diff verdict, and the judge
hash into one record.  It never invents a verdict; a missing product or a
timeout remains non-covered.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

import semantic_diff as sd

TOOL_VERSION = "1.0.0"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXIT_FOR_STATUS = {
    sd.EQUAL: 0,
    sd.DIFFERENT: 1,
    sd.INCONCLUSIVE: 2,
    sd.ERROR: 3,
}


def sha256_file(path: str):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def norm_path(value: str) -> str:
    value = (value or "").replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    return value


def abs_path(value: str) -> str:
    path = norm_path(value)
    if not path:
        return ""
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def rel_or_abs(path: str) -> str:
    try:
        return norm_path(os.path.relpath(os.path.abspath(path), ROOT))
    except ValueError:
        return os.path.abspath(path)


def load_space(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise ValueError("invalid judgment-space manifest")
    return data


def decompile(pyc: str, product: str, decompiler: str, timeout: float) -> tuple[bool, str, str]:
    os.makedirs(os.path.dirname(product), exist_ok=True)
    try:
        if os.path.exists(product):
            os.remove(product)
    except OSError:
        pass
    command = [sys.executable, "-X", "utf8", decompiler, pyc, "-o", product]
    try:
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                              timeout=timeout, encoding="utf-8", errors="replace")
        ok = proc.returncode == 0 and os.path.isfile(product) and os.path.getsize(product) > 0
        return ok, " ".join(command), (proc.stderr or proc.stdout or "").strip()[-1000:]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, " ".join(command), "%s: %s" % (type(exc).__name__, exc)


def make_record(entry: dict, product_root: str, decompiler: str, timeout: float,
                judge_sha: str, seed: int) -> tuple[dict | None, str]:
    eid = entry.get("id")
    source = abs_path(entry.get("p_j") or "")
    pyc = abs_path(entry.get("pyc") or "")
    if not isinstance(eid, str) or not eid:
        return None, "missing_id"
    if not source or not os.path.isfile(source) or os.path.getsize(source) == 0:
        return None, "c1_source_missing"
    if not pyc or not os.path.isfile(pyc):
        return None, "c2_pyc_missing"
    source_sha = sha256_file(source)
    pyc_sha = sha256_file(pyc)
    if not source_sha or not pyc_sha:
        return None, "hash_unreadable"
    input_model = entry.get("input_model") if isinstance(entry.get("input_model"), dict) else {}
    raw_calls = input_model.get("calls")
    calls = [str(item).strip() for item in raw_calls
             if isinstance(item, str) and str(item).strip()] if isinstance(raw_calls, list) else []
    product = os.path.join(product_root, eid.replace("/", "_") + ".py")
    product_abs = os.path.join(ROOT, product)
    ok, command, decompile_note = decompile(pyc, product_abs, decompiler, timeout)
    record = {
        "entry_id": eid,
        "c1": {"path": rel_or_abs(source), "sha256": source_sha,
               "lines": len(open(source, "r", encoding="utf-8-sig", errors="replace").read().splitlines())},
        "c2": {"pyc_path": rel_or_abs(pyc), "sha256": pyc_sha,
               "python_version": sys.version.split()[0]},
        "input_model": {"kind": input_model.get("kind") or "module", "calls": calls},
        "status": "probe_only",
        "note": decompile_note,
    }
    if not ok:
        record["reason"] = "decompile_failed"
        return record, "decompile_failed"
    product_sha = sha256_file(product_abs)
    if not product_sha:
        record["reason"] = "product_unreadable"
        return record, "product_unreadable"
    record["c3"] = {"product_path": rel_or_abs(product_abs), "sha256": product_sha,
                    "command": command}
    case = {
        "case_id": eid,
        "original": {"pyc": pyc},
        "product": {"source": product_abs},
        "entrypoint": "module",
        "args": [],
        "kwargs": {},
        "timeout_s": timeout,
        "_base": ROOT,
    }
    if calls:
        # Task 1.1: input_model.calls carries the callability dimension; the
        # judge evaluates each expression in the module namespace.
        case["call_exprs"] = calls
    else:
        case["entrypoint"] = entry.get("entrypoint") or "module"
    try:
        result = sd.compare_case(case)
    except BaseException as exc:
        result = {"status": sd.ERROR, "errors": ["%s: %s" % (type(exc).__name__, exc)],
                  "diffs": [], "inconclusive": []}
    verdict = result.get("status") if result.get("status") in EXIT_FOR_STATUS else sd.ERROR
    record["c4"] = {"verdict": verdict, "seed": seed,
                    "exit_code": EXIT_FOR_STATUS[verdict],
                    "diffs": [d.get("dimension") for d in result.get("diffs", [])
                              if isinstance(d, dict)],
                    "errors": result.get("errors", [])[:10],
                    "inconclusive": result.get("inconclusive", [])[:10]}
    record["c5"] = {"source_sha256": source_sha, "pyc_sha256": pyc_sha,
                    "product_sha256": product_sha, "judge_sha256": judge_sha,
                    "runner_version": "semantic_runner/%s" % TOOL_VERSION}
    if verdict in (sd.INCONCLUSIVE, sd.ERROR):
        record["status"] = "unexecuted"
    elif not calls:
        # Task 1.1: module-only entries never count as covered_5tuple; the
        # measured verdict stays recorded as defect evidence.
        record["status"] = "probe_only"
        record["reason"] = "module_only"
    else:
        record["status"] = "covered_5tuple"
    return record, verdict


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report", default="")
    parser.add_argument("--product-dir", default="",
                        help="default: <space-dir>/semantic_products")
    parser.add_argument("--decompiler", default=os.path.join(ROOT, "pycdc.py"))
    parser.add_argument("--judge", default=os.path.join(ROOT, "tools", "completeness",
                                                        "semantic_diff.py"))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--seconds", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args(argv)

    try:
        space = load_space(args.space)
    except Exception as exc:
        print("[semantic_runner] ERROR: %s" % exc, file=sys.stderr)
        return 2
    judge_sha = sha256_file(args.judge)
    if not judge_sha:
        print("[semantic_runner] ERROR: cannot read judge %s" % args.judge, file=sys.stderr)
        return 2
    product_root = args.product_dir or os.path.join(
        os.path.dirname(os.path.abspath(args.space)), "semantic_products")
    entries = [entry for entry in space["entries"] if isinstance(entry, dict)]
    entries = entries[args.offset:]
    if args.limit > 0:
        entries = entries[:args.limit]
    records = []
    skipped = {}
    started = time.monotonic()
    stopped = "case_limit"
    for entry in entries:
        if args.seconds > 0 and time.monotonic() - started >= args.seconds:
            stopped = "time_budget"
            break
        record, reason = make_record(entry, rel_or_abs(product_root), args.decompiler,
                                     args.timeout, judge_sha, int((space.get("seed") or 0)))
        if record is None:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        records.append(record)
        print("[semantic_runner] %-16s %-16s %-14s %s" % (record["entry_id"],
                                                          record.get("c4", {}).get("verdict", "-"),
                                                          record.get("status", "-"),
                                                          record.get("reason", "")))
    if len(entries) and len(records) < len(entries) and stopped == "case_limit":
        stopped = "skipped"
    counts = {}
    for record in records:
        verdict = record.get("c4", {}).get("verdict", "NO_C4")
        counts[verdict] = counts.get(verdict, 0) + 1
    module_only = sum(1 for record in records if record.get("reason") == "module_only")
    covered = sum(1 for record in records if record.get("status") == "covered_5tuple")
    payload = {"tool": "semantic_runner", "version": TOOL_VERSION, "space": norm_path(args.space),
               "judge_sha256": judge_sha, "records": records,
               "summary": {"total": len(records), "verdicts": counts, "skipped": skipped,
                           "stopped": stopped, "module_only": module_only,
                           "covered_5tuple": covered}}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload["summary"], fh, ensure_ascii=False, indent=1)
            fh.write("\n")
    print("[semantic_runner] records=%d verdicts=%s skipped=%s stopped=%s "
          "module_only=%d covered_5tuple=%d"
          % (len(records), counts, skipped, stopped, module_only, covered))
    return 0 if counts.get(sd.ERROR, 0) == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
