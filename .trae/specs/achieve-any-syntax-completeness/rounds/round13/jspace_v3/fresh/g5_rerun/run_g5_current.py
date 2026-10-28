#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the G5 battery on the current tree and emit gate-compatible evidence.

Inputs are the frozen 402/small34 indexes, remapped by
``remap_baseline_indexes.py`` (the frozen ``path`` fields point at another
checkout; only ``path`` is rewritten, ``rel``/``size`` stay frozen).

This runner does not regenerate products: ``pyc_verify.py batch`` compares each
pyc with the in-place ``*OK.py`` product, exactly as the rr-v5r06 G5 run did.
Every command, its return code, and its output tail are archived under
``out/`` and the aggregate is written to ``g5_regression_current.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SIX_TESTS = [
    "tests/test_algorithm_correctness.py",
    "tests/test_deep_nesting_pressure.py",
    "tests/test_control_flow_completeness_matrix.py",
    "tests/test_complete_syntax_coverage.py",
    "tests/test_boundary_cases.py",
    "tests/test_core_functional.py",
    "tests/test_repo_tool_hygiene.py",
]
EXPECTED_PYTEST = "2 failed, 282 passed, 2 xpassed"


def repo_root(start: str) -> str:
    cur = os.path.abspath(start)
    while not os.path.isdir(os.path.join(cur, "core", "cfg")):
        parent = os.path.dirname(cur)
        if parent == cur:
            raise SystemExit("cannot locate repo root from %s" % start)
        cur = parent
    return cur


def load(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args, cwd, timeout, label, log):
    t0 = time.time()
    try:
        proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=timeout)
        rc = proc.returncode
        out = (proc.stdout or "") + (("\n[stderr] " + proc.stderr)
                                     if proc.stderr else "")
    except subprocess.TimeoutExpired as exc:
        rc = "TIMEOUT"
        out = "[TIMEOUT] %s" % str(exc)[:300]
    elapsed = round(time.time() - t0, 1)
    with open(log, "a", encoding="utf-8") as fh:
        fh.write("=== %s rc=%s %.1fs\n%s\n" % (label, rc, elapsed, out[-4000:]))
    print("=== %s rc=%s %.1fs" % (label, rc, elapsed), flush=True)
    return rc, out, elapsed


def bom_state(path):
    with open(path, "rb") as fh:
        head = fh.read(8)
    if head.startswith(b"\xef\xbb\xbf\xef\xbb\xbf"):
        return "multiple"
    if head.startswith(b"\xef\xbb\xbf"):
        return "one"
    return "none"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="")
    parser.add_argument("--out", default=os.path.join(HERE, "out"))
    args = parser.parse_args(argv)
    root = repo_root(args.root or HERE)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    log = os.path.join(out, "run_log.txt")
    open(log, "w", encoding="utf-8").close()
    py = sys.executable
    evidence = {
        "tool": "g5_current_runner",
        "version": "1.0.0",
        "root": root.replace("\\", "/"),
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "commands": [],
    }
    shards = []
    total_units_success = total_units_total = total_files = 0
    files_by_status = {"success": 0, "failure": 0,
                       "compile_error": 0, "error": 0}
    for i in range(8):
        index = os.path.join(HERE, "shards", "shard%d.json" % i)
        report = os.path.join(out, "shard%d_report.json" % i)
        cmd = [py, "-X", "utf8", "scripts/pyc_verify.py", "batch",
               "--index", index, "--json", report]
        rc, stdout, elapsed = run(cmd, root, 900, "SHARD%d" % i, log)
        row = {"shard": i, "rc": rc, "elapsed_sec": elapsed,
               "index": index.replace("\\", "/"),
               "report": report.replace("\\", "/"),
               "tail": stdout.strip().splitlines()[-1:]}
        if rc == 0 and os.path.isfile(report):
            payload = load(report)
            rows = payload.get("rows") or []
            row.update({
                "files_total": payload.get("files_total", len(rows)),
                "units_success": payload.get("units_success",
                                             sum(r.get("units_success", 0) for r in rows)),
                "units_total": payload.get("units_total",
                                           sum(r.get("units_total", 0) for r in rows)),
                "files_by_status": payload.get("files_by_status", {}),
                "ruler": payload.get("ruler", {}),
            })
            total_units_success += int(row["units_success"] or 0)
            total_units_total += int(row["units_total"] or 0)
            total_files += int(row.get("files_total") or 0)
            for key in files_by_status:
                files_by_status[key] += int(
                    (row.get("files_by_status") or {}).get(key, 0))
        shards.append(row)
        evidence["commands"].append({"label": "SHARD%d" % i, "rc": rc,
                                     "elapsed_sec": elapsed,
                                     "command": [str(x) for x in cmd]})

    small_index = os.path.join(HERE, "shards", "small34.json")
    small_report = os.path.join(out, "small34_report.json")
    cmd = [py, "-X", "utf8", "scripts/pyc_verify.py", "batch",
           "--index", small_index, "--json", small_report]
    rc, stdout, elapsed = run(cmd, root, 600, "SMALL34", log)
    small = {"rc": rc, "elapsed_sec": elapsed,
             "index": small_index.replace("\\", "/"),
             "report": small_report.replace("\\", "/"),
             "tail": stdout.strip().splitlines()[-1:]}
    if rc == 0 and os.path.isfile(small_report):
        payload = load(small_report)
        rows = payload.get("rows") or []
        small.update({
            "files_total": payload.get("files_total", len(rows)),
            "units_success": payload.get("units_success",
                                         sum(r.get("units_success", 0) for r in rows)),
            "units_total": payload.get("units_total",
                                       sum(r.get("units_total", 0) for r in rows)),
            "files_by_status": payload.get("files_by_status", {}),
        })
    evidence["commands"].append({"label": "SMALL34", "rc": rc,
                                 "elapsed_sec": elapsed,
                                 "command": [str(x) for x in cmd]})

    quotation_pyc = os.path.join(root, "site-packages", "fly", "data", "quotation.pyc")
    cmd = [py, "-X", "utf8", "scripts/pyc_verify.py", "single", quotation_pyc]
    rc, stdout, elapsed = run(cmd, root, 300, "QUOTATION", log)
    tail_lines = [line for line in stdout.strip().splitlines() if line.strip()]
    quotation = {"rc": rc, "elapsed_sec": elapsed,
                 "tail": tail_lines[-1] if tail_lines else "",
                 "units": (re.search(r"units=(\d+)/(\d+)", stdout or "").groups()
                           if re.search(r"units=(\d+)/(\d+)", stdout or "") else None)}
    evidence["commands"].append({"label": "QUOTATION", "rc": rc,
                                 "elapsed_sec": elapsed,
                                 "command": [str(x) for x in cmd]})

    cmd = [py, "-X", "utf8", "-m", "pytest"] + SIX_TESTS + [
        "-p", "no:cacheprovider", "--tb=no", "-q"]
    rc, stdout, elapsed = run(cmd, root, 900, "TESTS7", log)
    summary_line = ""
    for line in reversed(stdout.strip().splitlines()):
        if re.search(r"\d+ (failed|passed|error)", line):
            summary_line = line.strip()
            break
    failed_names = sorted(set(re.findall(r"FAILED (\S+)", stdout or "")))
    pytest = {"rc": rc, "elapsed_sec": elapsed, "summary_line": summary_line,
              "failed_names": failed_names,
              "matches_expected_prefix": summary_line.startswith(EXPECTED_PYTEST)}
    evidence["commands"].append({"label": "TESTS7", "rc": rc,
                                 "elapsed_sec": elapsed,
                                 "command": [str(x) for x in cmd]})

    iv2 = {}
    cmd = [py, "-X", "utf8", "-c",
           "import core.pyc_loader_v2, core.control_flow, core.cfg, "
           "core.cfg.region_analyzer, core.cfg.region_ast_generator, "
           "core.cfg.cfg_builder, core.cfg.basic_block, bytecode.pyc_disasm; "
           "print('IMPORT_OK')"]
    rc, stdout, elapsed = run(cmd, root, 120, "IV2_IMPORT", log)
    iv2["IMPORT_OK"] = rc == 0 and (stdout or "").strip().endswith("IMPORT_OK")
    iv2["BOM_region_analyzer.py"] = bom_state(
        os.path.join(root, "core", "cfg", "region_analyzer.py"))
    iv2["BOM_region_ast_generator.py"] = bom_state(
        os.path.join(root, "core", "cfg", "region_ast_generator.py"))
    try:
        for rel in ("core/cfg/region_analyzer.py", "core/cfg/region_ast_generator.py"):
            with open(os.path.join(root, rel), encoding="utf-8-sig") as fh:
                compile(fh.read(), rel, "exec")
        iv2["COMPILE_OK"] = True
    except Exception as exc:
        iv2["COMPILE_OK"] = "%s: %s" % (type(exc).__name__, exc)

    diff = subprocess.run(["git", "diff", "--unified=0", "HEAD", "--", "core/cfg"],
                          cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60)
    added = [line[1:] for line in (diff.stdout or "").splitlines()
             if line.startswith("+") and not line.startswith("+++")]
    forbidden = [line.strip()[:160] for line in added
                 if re.search(r"def\s+(_fix_|_merge_|_patch_|_fallback_|"
                              r"_hack_|_workaround_|_temp_)", line)]
    status = subprocess.run(["git", "status", "--porcelain", "--", "core/cfg"],
                            cwd=root, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=60)
    iv2["G3_forbidden_prefix_new_defs"] = len(forbidden)
    iv2["G3_forbidden_examples"] = forbidden
    evidence["core_cfg_clean"] = not (status.stdout or "").strip()
    evidence["core_cfg_status"] = (status.stdout or "").strip()

    payload = {
        "total": {
            "units_success": total_units_success,
            "units_total": total_units_total,
            "files_total": total_files,
            "files_failure": files_by_status["failure"],
            "files_by_status": files_by_status,
        },
        "shards": shards,
        "small34": {
            "units_success": small.get("units_success", 0),
            "units_total": small.get("units_total", 0),
            "files_total": small.get("files_total", 0),
            "files_by_status": small.get("files_by_status", {}),
            "rc": small.get("rc"),
        },
        "quotation": quotation,
        "pytest": pytest,
        "iv2": iv2,
        "core_cfg_clean": evidence["core_cfg_clean"],
        "run_meta": evidence,
        "note": ("Current-tree G5 rerun after B275; indexes remapped by "
                 "remap_baseline_indexes.py (path only). Products are the "
                 "in-place *OK.py files compared by the frozen pyc_verify."),
    }
    payload["run_meta"]["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    out_json = os.path.join(out, "g5_regression_current.json")
    with open(out_json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[g5] 402=%s/%s small34=%s/%s quotation=%s pytest=%r"
          % (total_units_success, total_units_total,
             payload["small34"]["units_success"],
             payload["small34"]["units_total"], quotation.get("tail"),
             summary_line), flush=True)
    ok = (total_units_success == 6617 and total_units_total == 6617
          and files_by_status["failure"] == 0
          and payload["small34"]["units_success"] == 1568
          and payload["small34"]["units_total"] == 1568
          and quotation.get("rc") == 0
          and "153/153" in (quotation.get("tail") or "")
          and summary_line.startswith(EXPECTED_PYTEST)
          and iv2.get("IMPORT_OK") is True
          and iv2.get("COMPILE_OK") is True
          and iv2.get("G3_forbidden_prefix_new_defs") == 0
          and iv2.get("BOM_region_ast_generator.py") == "one"
          and iv2.get("BOM_region_analyzer.py") == "one"
          and evidence["core_cfg_clean"])
    print("[g5] gate_inputs_green=%s -> %s" % (ok, out_json), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
