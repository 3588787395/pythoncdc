#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure the five behaviour-diff minimal repros (fresh/gap_g2/repro).

For each g2c_REAL46-*_min.py:
  1. compile it to a .pyc (origin artifact);
  2. decompile that .pyc with the CURRENT tree (pycdc.py);
  3. judge original.pyc vs product.py with tools/completeness/semantic_diff.py;
  4. control run: judge original.pyc vs a BYTE-IDENTICAL copy of the source
     placed in repro/elsewhere/ (isolates observation-layer artifacts);
  5. scripts/pyc_verify.py single --source <product>.

Read-only w.r.t. the product/tool trees; writes only under fresh/gap_g2/.
"""
from __future__ import annotations

import json
import os
import py_compile
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
HERE = os.path.join(ROOT, "fresh", "gap_g2", "repro")
OUT = os.path.join(HERE, "out")
ELSE = os.path.join(HERE, "elsewhere")
PY = sys.executable
sys.path.insert(0, os.path.join(ROOT, "tools", "completeness"))
import semantic_diff as sd  # noqa: E402

UNITS = ["REAL46-004", "REAL46-023", "REAL46-031", "REAL46-022", "REAL46-046"]


def sh(args, **kw):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", **kw)


def dims(diffs):
    out = {}
    for d in diffs:
        key = d.get("dimension")
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


def judge(pyc, product):
    case = {"case_id": os.path.basename(product), "original": {"pyc": pyc},
            "product": {"source": product}, "entrypoint": "module",
            "args": [], "kwargs": {}, "timeout_s": 20, "_base": ROOT}
    res = sd.compare_case(case)
    return {"status": res.get("status"), "dims": dims(res.get("diffs") or []),
            "diffs": (res.get("diffs") or [])[:12],
            "errors": res.get("errors") or [], "inconclusive": res.get("inconclusive") or []}


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(ELSE, exist_ok=True)
    report = {"python": sys.version.split()[0],
              "judge_sha256": sd._sha_file(os.path.join(ROOT, "tools", "completeness",
                                                        "semantic_diff.py")),
              "units": []}
    for uid in UNITS:
        src = os.path.join(HERE, "g2c_%s_min.py" % uid)
        pyc = os.path.join(HERE, "__pycache__", "g2c_%s_min.cpython-311.pyc" % uid)
        prod = os.path.join(OUT, "g2c_%s_min.py" % uid)
        copy = os.path.join(ELSE, "g2c_%s_min.py" % uid)
        row = {"unit": uid, "source": os.path.relpath(src, ROOT), "source_lines":
               len(open(src, encoding="utf-8").read().splitlines())}
        if os.path.exists(pyc):
            os.remove(pyc)
        try:
            py_compile.compile(src, cfile=pyc, doraise=True)
            row["compile"] = "ok"
        except py_compile.PyCompileError as exc:
            row["compile"] = "FAILED: %s" % exc
            report["units"].append(row)
            continue
        if os.path.exists(prod):
            os.remove(prod)
        dec = sh([PY, "-X", "utf8", os.path.join(ROOT, "pycdc.py"), pyc, "-o", prod])
        row["decompile_rc"] = dec.returncode
        row["product"] = os.path.relpath(prod, ROOT)
        row["product_lines"] = (len(open(prod, encoding="utf-8").read().splitlines())
                                if os.path.isfile(prod) else 0)
        comp = sh([PY, "-X", "utf8", "-c",
                   "import py_compile,sys;py_compile.compile(sys.argv[1],doraise=True)",
                   prod])
        row["product_compiles"] = comp.returncode == 0
        row["product_stderr"] = (comp.stderr or "").strip().splitlines()[-1:] or [""]
        row["judge_current_product"] = judge(pyc, prod)
        shutil.copyfile(src, copy)
        row["judge_identical_source_elsewhere"] = judge(pyc, copy)
        ver = sh([PY, "-X", "utf8", os.path.join(ROOT, "scripts", "pyc_verify.py"),
                  "single", pyc, "--source", prod])
        row["pyc_verify_rc"] = ver.returncode
        row["pyc_verify"] = [ln for ln in (ver.stdout or "").splitlines()
                             if ln.startswith("[single]") or ln.strip().startswith("status")]
        report["units"].append(row)
        print("%-13s product_compiles=%-5s judge=%-10s artifact_control=%s"
              % (uid, row["product_compiles"],
                 row["judge_current_product"]["status"],
                 row["judge_identical_source_elsewhere"]["status"]))
        print("   dims=%s  control_dims=%s"
              % (row["judge_current_product"]["dims"],
                 row["judge_identical_source_elsewhere"]["dims"]))
        for ln in row["pyc_verify"]:
            print("   " + ln)
    with open(os.path.join(ROOT, "fresh", "gap_g2", "repro", "min_repro_results.json"),
              "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
