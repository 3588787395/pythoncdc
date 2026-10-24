#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Non-vacuous self-test for tools/completeness/semantic_diff.py.

Each case exercises a distinct observable dimension.  The test asserts the
expected status and, for DIFFERENT cases, at least one expected dimension.
It also proves that structural formatting changes (comments/blank lines) do
not create false positives, while docstring loss and float tolerance are
handled explicitly.
"""

from __future__ import annotations

import json
import os
import py_compile
import shutil
import sys
import tempfile

import semantic_diff as sd


def write(root: str, name: str, text: str) -> str:
    path = os.path.join(root, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return path


def pair(root: str, name: str, original: str, product: str, **overrides) -> dict:
    folder = os.path.join(root, name)
    os.makedirs(folder, exist_ok=True)
    case = {
        "case_id": name,
        "original": {"source": write(folder, "original.py", original)},
        "product": {"source": write(folder, "product.py", product)},
        "entrypoint": "function:f",
        "args": [],
        "timeout_s": 6,
    }
    case.update(overrides)
    return case


def pyc_pair(root: str, name: str, source: str) -> dict:
    folder = os.path.join(root, name)
    os.makedirs(folder, exist_ok=True)
    source_path = write(folder, "original.py", source)
    pyc_path = os.path.join(folder, "original.pyc")
    py_compile.compile(source_path, cfile=pyc_path, doraise=True, optimize=0)
    return {
        "case_id": name,
        "original": {"pyc": pyc_path},
        "product": {"source": write(folder, "product.py", source)},
        "entrypoint": "function:f",
        "args": [4],
        "timeout_s": 6,
    }


def main() -> int:
    root = tempfile.mkdtemp(prefix="semantic_diff_selftest_")
    cases = []
    try:
        cases.append((pair(root, "equal-int", "def f(x):\n    return x + 1\n",
                            "def f(x):\n    return x + 1\n", args=[1]), sd.EQUAL, [], []))
        cases.append((pair(root, "type-int-bool", "def f():\n    return 1\n",
                            "def f():\n    return True\n"), sd.DIFFERENT, ["R1"], []))
        cases.append((pair(root, "float-tolerance",
                            "def f():\n    return 0.30000000000000004\n",
                            "def f():\n    return 0.3\n",
                            tolerance={"float_abs_tol": 1e-12}), sd.EQUAL, [],
                      ["$.call[0].return"]))
        cases.append((pair(root, "docstring-loss", 'def f():\n    """kept"""\n    return 1\n',
                            "def f():\n    return 1\n"), sd.DIFFERENT, ["R7"], []))
        cases.append((pair(root, "format-only", '"""doc"""\n\n# layout\ndef f(x):\n    return x\n',
                            '"""doc"""\ndef f(x):\n    return x\n', args=[3]), sd.EQUAL, [], []))
        cases.append((pair(root, "signature-default", "def f(x, y=1):\n    return x\n",
                            "def f(x, y=2):\n    return x\n", args=[3]), sd.DIFFERENT, ["R7"], []))
        cases.append((pair(root, "exception-message",
                            "def f():\n    raise ValueError('a')\n",
                            "def f():\n    raise ValueError('b')\n"), sd.DIFFERENT, ["R6"], []))
        cases.append((pair(root, "side-effect",
                            "def f(x):\n    x.append(1)\n    return x\n",
                            "def f(x):\n    x.append(2)\n    return x\n", args=[[]]),
                      sd.DIFFERENT, ["R5"], []))
        cases.append((pair(root, "stdout-order",
                            'def f():\n    print("a")\n    print("b")\n',
                            'def f():\n    print("b")\n    print("a")\n'),
                      sd.DIFFERENT, ["R2", "R4"], []))
        cases.append((pair(root, "file-effect",
                            'def f():\n    open("out.txt", "w").write("a")\n',
                            'def f():\n    open("out.txt", "w").write("b")\n'),
                      sd.DIFFERENT, ["R5"], []))
        cases.append((pair(root, "module-diff", "x = 1\n", "x = True\n", entrypoint="module"),
                      sd.DIFFERENT, ["R5"], []))
        cases.append((pair(root, "async-equal",
                            "async def f(x):\n    return x + 1\n",
                            "async def f(x):\n    return x + 1\n", args=[2]),
                      sd.EQUAL, [], []))
        cases.append((pair(root, "class-equal",
                            "class C:\n    def __init__(self, x):\n        self.x = x\n",
                            "class C:\n    def __init__(self, x):\n        self.x = x\n",
                            entrypoint="class:C", args=[2]), sd.EQUAL, [], []))
        cases.append((pair(root, "binding-inconclusive",
                            "def f(x):\n    return x\n", "def f(x):\n    return x\n"),
                      sd.INCONCLUSIVE, [], []))
        cases.append((pair(root, "product-import-failure", "x = 1\n",
                            "raise RuntimeError('boom')\n", entrypoint="module"),
                      sd.DIFFERENT, ["LOAD"], []))
        cases.append((pyc_pair(root, "pyc-equal", "def f(x):\n    return x + 1\n"),
                      sd.EQUAL, [], []))
        broken = {
            "case_id": "missing-original",
            "original": {"source": os.path.join(root, "nope.py")},
            "product": {"source": write(root, "missing-product.py", "def f():\n    return 1\n")},
            "entrypoint": "function:f",
        }
        cases.append((broken, sd.ERROR, [], []))

        # Task 1 measurement semantics (achieve-any-syntax-completeness).
        cases.append((pair(root, "module-only-equal", "x = 1\n", "x = 1\n",
                           entrypoint="module"), sd.EQUAL, [], []))
        cases.append((pair(root, "call-exprs-equal",
                           "def g(x):\n    return x * 2\n",
                           "def g(x):\n    return x * 2\n",
                           entrypoint="module", call_exprs=["g(2)"]), sd.EQUAL, [], []))
        cases.append((pair(root, "call-exprs-r1",
                           "def g(x):\n    return x * 2\n",
                           "def g(x):\n    return x * 3\n",
                           entrypoint="module", call_exprs=["g(2)"]),
                      sd.DIFFERENT, ["R1"], []))
        cases.append((pair(root, "call-exprs-missing-function",
                           "def g(x):\n    return x\n",
                           "pass\n",
                           entrypoint="module", call_exprs=["g(2)"]),
                      sd.DIFFERENT, ["R6"], []))
        cases.append((pair(root, "r7-plus-r1",
                           "def g(x):\n    return x + 1\n",
                           "def g(x):\n    y = x + 2\n    return y\n",
                           entrypoint="module", call_exprs=["g(1)"]),
                      sd.DIFFERENT, ["R1", "R7"], []))
        cases.append((pair(root, "r7-protected-tolerance",
                           "def g(x):\n    return x + 1\n",
                           "def g(x):\n    return x + 2\n",
                           entrypoint="module",
                           tolerance={"ignore_metadata_fields": ["metadata.code.co_code"]}),
                      sd.ERROR, [], []))
        cases.append((pair(root, "r7-ancestor-tolerance",
                           "def g(x):\n    return x + 1\n",
                           "def g(x):\n    return x + 2\n",
                           entrypoint="module",
                           tolerance={"ignore_metadata_fields": ["$.metadata.code"]}),
                      sd.ERROR, [], []))
        cases.append((pair(root, "timeout-product",
                           "x = 1\n",
                           "import time\ntime.sleep(30)\n",
                           entrypoint="module", timeout_s=1),
                      sd.INCONCLUSIVE, [], [], ["product execution timed out"]))
        cases.append((pair(root, "timeout-original",
                           "import time\ntime.sleep(30)\n",
                           "x = 1\n",
                           entrypoint="module", timeout_s=1),
                      sd.INCONCLUSIVE, [], [], ["original execution timed out"]))

        results = []
        failures = 0
        for case, expected, dimensions, tolerances, *rest in cases:
            expect_inconclusive = rest[0] if rest else []
            result = sd.compare_case(case)
            actual = result["status"]
            found = sorted({item.get("dimension") for item in result.get("diffs", [])})
            missing = [dim for dim in dimensions if dim not in found]
            missing_tol = [path for path in tolerances if not any(path in item for item in result.get("tolerances", []))]
            missing_inconclusive = [text for text in expect_inconclusive
                                    if not any(text in item for item in result.get("inconclusive", []))]
            ok = (actual == expected and not missing and not missing_tol
                  and not missing_inconclusive)
            if not ok:
                failures += 1
            results.append({
                "case_id": case["case_id"],
                "expected": expected,
                "actual": actual,
                "expected_dimensions": dimensions,
                "observed_dimensions": found,
                "missing_dimensions": missing,
                "missing_tolerances": missing_tol,
                "missing_inconclusive": missing_inconclusive,
                "tolerances": result.get("tolerances", []),
                "errors": result.get("errors", []),
                "inconclusive": result.get("inconclusive", []),
                "ok": ok,
            })
        payload = {"tool": "semantic_diff_selftest", "total": len(results),
                   "passed": len(results) - failures, "failed": failures, "results": results}
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 0 if failures == 0 else 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
