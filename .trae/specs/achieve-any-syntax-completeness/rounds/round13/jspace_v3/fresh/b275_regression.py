#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B275 regression: nested try/except/finally inside an outer try.

The defect: for ``try: try: for ...: with ...: except ValueError: ...
finally: DONE = 1`` the region analyzer records the inner finally's
``finally_copy_blocks`` as empty (the normal-copy exit is protected by the
outer handler), so the W13 marker-NOP counter added an extra inner ``try``
around the ``for``.  R7 then differed (``co_code`` 300 vs 298 and
``co_exceptiontable``).

This script decompiles the repaired m04 pyc and three controls and compares
the recompiled code objects recursively.  It is evidence, not a test baseline.

Run from the repository root:

    python -X utf8 .../fresh/b275_regression.py
"""

from __future__ import annotations

import marshal
import os
import py_compile
import subprocess
import sys
import tempfile
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..", ".."))
FRESH = os.path.dirname(os.path.abspath(__file__))


def load_code(path: str) -> types.CodeType:
    with open(path, "rb") as fh:
        data = fh.read()
    return marshal.loads(data[16:])


def code_equal(a: types.CodeType, b: types.CodeType, path: str = "<module>") -> list[str]:
    diffs: list[str] = []
    for attr in ("co_code", "co_exceptiontable", "co_names", "co_varnames", "co_flags"):
        if getattr(a, attr) != getattr(b, attr):
            diffs.append("%s.%s" % (path, attr))
    if len(a.co_consts) != len(b.co_consts):
        diffs.append("%s.co_consts.len %d vs %d" % (path, len(a.co_consts), len(b.co_consts)))
        return diffs
    for index, (left, right) in enumerate(zip(a.co_consts, b.co_consts)):
        left_code = isinstance(left, types.CodeType)
        right_code = isinstance(right, types.CodeType)
        if left_code != right_code:
            diffs.append("%s.co_consts[%d] code/type mismatch" % (path, index))
            continue
        if left_code:
            diffs.extend(code_equal(left, right, "%s/%s" % (path, left.co_name)))
        elif left != right:
            diffs.append("%s.co_consts[%d] %r vs %r" % (path, index, left, right))
    return diffs


def decompile(pyc: str, out: str) -> None:
    subprocess.run(
        [sys.executable, "-X", "utf8", os.path.join(ROOT, "pycdc.py"), "--region", "-o", out, pyc],
        check=True,
        cwd=ROOT,
    )


def recompile(source: str, work: str, name: str) -> str:
    src = os.path.join(work, name + ".py")
    pyc = os.path.join(work, name + ".pyc")
    with open(src, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(source)
    py_compile.compile(src, cfile=pyc, doraise=True)
    return pyc


def find_code(code: types.CodeType, name: str) -> types.CodeType | None:
    for item in code.co_consts:
        if isinstance(item, types.CodeType):
            if item.co_name == name:
                return item
            found = find_code(item, name)
            if found is not None:
                return found
    return None


def check_case(label: str, original_pyc: str, work: str, code_name: str | None = None) -> bool:
    product = os.path.join(work, label + ".py")
    decompile(original_pyc, product)
    with open(product, "r", encoding="utf-8") as fh:
        source = fh.read()
    product_pyc = recompile(source, work, label)
    original = load_code(original_pyc)
    recompiled = load_code(product_pyc)
    if code_name:
        original = find_code(original, code_name)
        recompiled = find_code(recompiled, code_name)
        if original is None or recompiled is None:
            print("[B275] %-18s MISSING code object %s" % (label, code_name))
            return False
    diffs = code_equal(original, recompiled, "<module>" if code_name is None else code_name)
    if diffs:
        print("[B275] %-18s DIFFERENT %s" % (label, diffs[:8]))
        return False
    print("[B275] %-18s EQUAL" % label)
    return True


def main() -> int:
    work = tempfile.mkdtemp(prefix="b275_")
    cases = [
        ("m04_module_try", os.path.join(FRESH, "repaired_pyc", "m04_module_try.pyc"), None),
        ("c04_CTryNest", os.path.join(ROOT, "test_repros", "round2", "c04_class_try.pyc"), "CTryNest"),
    ]
    # Control: a flat try/except/finally must not acquire an extra try.
    control_src = (
        "def f():\n"
        "    try:\n"
        "        x = 1\n"
        "    except ValueError:\n"
        "        x = 2\n"
        "    finally:\n"
        "        y = 3\n"
    )
    control_pyc = recompile(control_src, work, "control_flat")
    cases.append(("control_flat", control_pyc, "f"))

    ok = True
    for label, pyc, code_name in cases:
        ok = check_case(label, pyc, work, code_name) and ok
    print("[B275] %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
