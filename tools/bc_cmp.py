#!/usr/bin/env python3
"""Generic per-function bytecode comparison harness for pythoncdc.

Usage:
    python tools/bc_cmp.py <path/to/file.pyc> [--out DIR]

For each code object (function/method/<module>) in the pyc:
  1. decompile the pyc with pycdc.decompile_pyc
  2. recompile the decompiled source with compile()
  3. compare original vs recompiled bytecode instruction-by-instruction
  4. report PASS/FAIL per function with a short diff of first discrepancies

Exit code 0 if all functions match, 1 otherwise.
"""
import os
import sys
import marshal
import types
import dis
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode


def iter_code_objects(code, prefix=""):
    name = prefix + code.co_name if prefix else code.co_name
    yield name, code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            sub = name + "." if name != "<module>" else ""
            yield from iter_code_objects(const, sub)


def load_code(pyc_path):
    with open(pyc_path, "rb") as f:
        data = f.read()
    # skip 16-byte header (Python 3.7+)
    return marshal.loads(data[16:])


def run_one(pyc_path, out_dir=None):
    """Decompile, recompile, and compare. Returns dict with 'funcs' map name->(ok, details)."""
    src = decompile_pyc(pyc_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(pyc_path))[0]
        with open(os.path.join(out_dir, base + "_decompiled.py"), "w", encoding="utf-8") as f:
            f.write(src)
    try:
        decomp_code = compile(src, "<decompiled>", "exec")
    except SyntaxError as e:
        return {"syntax_error": str(e), "funcs": {}}

    orig_code = load_code(pyc_path)
    funcs = {}
    for (oname, ocode), (dname, dcode) in zip(
        iter_code_objects(orig_code), iter_code_objects(decomp_code)
    ):
        if oname != dname:
            funcs[oname] = (False, {"name_mismatch": dname})
            continue
        res = compare_bytecode(ocode, dcode)
        ok = bool(res.get("match"))
        funcs[oname] = (ok, {
            "orig_count": res.get("orig_count"),
            "decomp_count": res.get("decomp_count"),
            "true_diffs": res.get("true_diffs") or [],
        })
    return {"funcs": funcs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pyc")
    ap.add_argument("--out", default=None, help="dir to write decompiled source")
    args = ap.parse_args()

    result = run_one(args.pyc, args.out)
    if "syntax_error" in result:
        print(f"SYNTAX ERROR in decompiled source: {result['syntax_error']}")
        sys.exit(2)

    total = 0
    passed = 0
    for oname, (ok, det) in result["funcs"].items():
        total += 1
        if ok:
            passed += 1
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {oname}  orig={det.get('orig_count')} decomp={det.get('decomp_count')} true_diffs={len(det.get('true_diffs') or [])}")
        if not ok and "name_mismatch" not in det:
            for d in det.get("true_diffs", [])[:8]:
                print("    " + str(d))

    print(f"\nSUMMARY: {passed}/{total} functions bytecode-match")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
