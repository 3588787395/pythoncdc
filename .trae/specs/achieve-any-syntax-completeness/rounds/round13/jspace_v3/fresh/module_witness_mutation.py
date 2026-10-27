#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mutation check for the module-code call witness.

The witness is only useful if it can distinguish a wrong product.  This script
compares the original ``m06_module_loops.pyc`` with:

1. the real decompiled product (expected ``EQUAL``);
2. a copy of that product with ``TOTAL += i`` changed to ``TOTAL -= i``
   (expected ``DIFFERENT`` with ``R5 module_values.TOTAL 103 vs 97``).

Run from the repository root:

    python -X utf8 .../fresh/module_witness_mutation.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.getcwd())
sys.path.insert(0, os.path.join(ROOT, "tools", "completeness"))
import semantic_diff as sd  # noqa: E402

EXPR = ("(lambda _c: __import__('types').FunctionType(_c, globals())())"
        "(__loader__.get_code(__name__))")


def compare(pyc: str, source: str) -> dict:
    case = {
        "case_id": "module-witness-mutation",
        "original": {"pyc": pyc},
        "product": {"source": source},
        "entrypoint": "module",
        "args": [],
        "kwargs": {},
        "timeout_s": 20.0,
        "call_exprs": [EXPR],
        "_base": ROOT,
    }
    return sd.compare_case(case)


def main() -> int:
    pyc = os.path.join(ROOT, "test_repros/round2/m06_module_loops.pyc")
    product = os.path.join(HERE, "semantic_products/module/JS-WHILE-024.py")
    if not os.path.isfile(product):
        raise SystemExit("missing product: %s" % product)
    text = open(product, "r", encoding="utf-8-sig").read()
    if "TOTAL += i" not in text:
        raise SystemExit("mutation anchor not found in %s" % product)
    tmp = tempfile.mkdtemp(prefix="module-witness-")
    try:
        good = os.path.join(tmp, "good.py")
        bad = os.path.join(tmp, "bad.py")
        shutil.copyfile(product, good)
        with open(bad, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text.replace("TOTAL += i", "TOTAL -= i", 1))
        good_result = compare(pyc, good)
        bad_result = compare(pyc, bad)
        print("[witness] product: %s" % good_result["status"])
        print("[witness] mutated: %s" % bad_result["status"])
        print("[witness] mutated diffs: %s"
              % json.dumps(bad_result.get("diffs"), ensure_ascii=False))
        if good_result["status"] != "EQUAL":
            raise SystemExit("real product is not EQUAL")
        if bad_result["status"] != "DIFFERENT":
            raise SystemExit("mutation was not detected")
        total = [d for d in bad_result.get("diffs", [])
                 if d.get("path") == "$.module_values.TOTAL.v"]
        if not total:
            raise SystemExit("mutation did not change module_values.TOTAL")
        print("[witness] PASS: mutation detected in module_values.TOTAL")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
