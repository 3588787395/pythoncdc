#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Materialise the G4 gap probes (round13 jspace_v3 / gate_gap).

Read-only w.r.t. core/: this script only writes probe sources into
``probes/`` next to this file.  Each probe is a valid Python 3.11 module with
at least one module-level zero-argument callable, so it is a legal J-space
``input_model.calls`` entry point.

Run:
    D:/Python/python.exe -I -X utf8 _build_probes.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "probes")

SOURCES = {}

# ---------------------------------------------------------------- cluster 1 --
# CodeGenerator._generate_dict_node (16 empty rules; node_type == X arms for
# statement node types).  The dict AST entry is what this cluster needs.
SOURCES["pj_dictnode_01"] = '''"""Module-level statement carrier for the dict-AST entry.

Covers node_type arms: Module / Assign / AnnAssign / AugAssign / Expr /
Pass / Delete / Global / Import / ImportFrom / Assert / FunctionDef /
AsyncFunctionDef / ClassDef / AsyncFor / Nonlocal.
"""
import os
import sys as _sys
from collections import OrderedDict

GLOBAL_SLOT = 0


def pj_entry():
    """Zero-arg entry: statement soup in a function body."""
    global GLOBAL_SLOT
    GLOBAL_SLOT = 1
    total = 0
    total += 1
    note: int = total
    del note
    if False:
        pass
    assert total == 1
    return OrderedDict([("a", 1), ("b", {"nested": [1, 2]})])


async def pj_entry_async(seq=()):
    """Zero-arg entry with an async-for over a dict/set literal."""
    async for item in seq:
        if item:
            return {"seen": item}
    return {}


def pj_entry_local():
    """Zero-arg entry with a nonlocal rebind."""
    slot = 0

    def inner():
        nonlocal slot
        slot = 1
        return slot

    return inner()


class PJHolder:
    """Zero-arg class whose body carries a dict literal statement."""

    TABLE = {"k": 1, "j": {2, 3}}
    PAIR = (1, 2)

    def method(self):
        return self.TABLE


def main():
    return pj_entry(), pj_entry_local(), PJHolder(), os.getcwd(), _sys.version_info


if __name__ == "__main__":
    main()
'''

SOURCES["pj_dictnode_02"] = '''"""Dict-AST carrier with the same statement arms nested one level deeper."""


def pj_entry():
    """Zero-arg entry: every statement arm inside a function body."""
    local = {"x": 1}

    def build():
        inner = {"y": 2}
        inner["z"] = local["x"]
        return inner

    class Nested:
        ATTR = {"n": [1, 2, 3]}

        def get(self):
            return self.ATTR

    del local["x"]
    return build(), Nested()


def pj_entry_comp(ns=(1, 2, 3)):
    """Zero-arg entry: dict/set/generator comprehensions."""
    d = {n: n * 2 for n in ns}
    s = {n + 1 for n in ns}
    g = (n - 1 for n in ns)
    return d, s, list(g)


def main():
    return pj_entry(), pj_entry_comp()


if __name__ == "__main__":
    main()
'''

SOURCES["pj_dictnode_03"] = '''"""Dict-AST carrier for match / try / yield / lambda statement arms."""


def pj_entry(v):
    """Zero-arg-callable entry: match statement over dict and tuple literals."""
    table = {1: "one", 2: "two"}
    match v:
        case {1: name}:
            return {"hit": name}
        case (a, b):
            return {"pair": [a, b]}
        case 0:
            return {}
        case _:
            return table


def pj_entry_try(fn):
    """Zero-arg-callable entry: try/except/else/finally with dict bodies."""
    try:
        out = {"step": "try"}
        fn(out)
    except (ValueError, KeyError):
        out = {"step": "except"}
    else:
        out = dict(out, step="else")
    finally:
        out = dict(out, step="finally")
    return out


def pj_entry_yield(ns=(1, -2, 0)):
    """Zero-arg entry: generator with yield / yield-from style arms."""
    for n in ns:
        if n > 0:
            yield {"sign": "+", "n": n}
        elif n < 0:
            yield {"sign": "-", "n": -n}
        else:
            yield {}


def pj_entry_lambda():
    """Zero-arg entry: lambdas kept in a dict literal."""
    fns = {"bump": lambda x: x + 1, "flip": lambda y: -y if y else 0}
    return fns["bump"](1), fns["flip"](0)


def main():
    return (pj_entry(1), pj_entry_try(dict), list(pj_entry_yield()),
            pj_entry_lambda())


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------- cluster 2 --
# ASTGeneratorV2._generate_if_ast (10 empty rules).  Only reachable through a
# dict-AST bridge (generate_ast_v2 / _decompile_nested_code), so the probes
# carry nested code objects whose bodies hold if/elif chains.
SOURCES["pj_v2if_01"] = '''"""Nested code objects whose bodies hold if/elif chains.

Targets ASTGeneratorV2._generate_if_ast (opcode wordings PRINT_ITEM /
PRINT_NEWLINE / PRINT_EXPR / GET_ATTR / BINARY_* and BINARY_OR/BINARY_AND
membership tests).  Nested code objects are the only documented bridge from
the region pipeline into generate_ast_v2.
"""


def pj_entry(n):
    """Zero-arg-callable entry: nested def with a two-arm if/elif chain."""

    def inner(v):
        if v > 1:
            return v * 2
        elif v == 1:
            return v + 1
        return 0

    return inner(n)


def pj_entry_deep(n):
    """Zero-arg-callable entry: if/elif chain over mixed binary operators."""

    def inner(v):
        if v % 2 == 0:
            return v // 2
        elif v / 2 > 1:
            return v / 2
        elif v - 1:
            return v - 1
        return v

    return inner(n)


def pj_entry_comp(ns=(1, 2, 3)):
    """Zero-arg entry: comprehension code objects with if filters."""
    a = [x for x in ns if x > 1]
    b = [y * 2 for y in ns if y % 2 and y or y + 1]
    return a, b


def pj_entry_lambda():
    """Zero-arg entry: lambda code objects holding conditional expressions."""
    f = lambda x: (x + 1) if x > 0 else (x - 1)
    g = lambda y: y and y or 0
    return f(1), g(2)


def main():
    return pj_entry(2), pj_entry_deep(4), pj_entry_comp(), pj_entry_lambda()


if __name__ == "__main__":
    main()
'''

SOURCES["pj_v2if_02"] = '''"""Class/method code objects whose bodies hold if/elif chains.

Second sample for ASTGeneratorV2._generate_if_ast, adding class-body and
decorator shapes so the bridge (if any) sees a class-level if chain too.
"""


def deco(fn):
    return fn


class PJBase:
    def method(self, v):
        if v:
            return 1
        elif not v:
            return 2
        return 3


class PJChild(PJBase):
    """Class body with an if chain, a lambda attribute and a nested class."""

    if True:
        FLAG = 1
    else:
        FLAG = 0

    HOOK = lambda self, x: x if x else -1

    class Nested:
        def go(self, y):
            if y and y > 0:
                return y * 2
            elif y or y == 0:
                return y + 2
            return -y


@deco
def pj_entry(n):
    """Zero-arg-callable entry: method call plus class-level if chain."""
    child = PJChild()
    return PJBase().method(n), PJChild.Nested().go(n), child.FLAG


def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    return pj_entry(2)

def main():
    return pj_entry(2), PJChild.HOOK(None, 1)


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------- cluster 3 --
# ASTGeneratorV2._generate_if_ast.extract_elif_chain (6 empty rules; symbols
# Break / While / For / Continue / Match / Try inside an elif-chain walker).
SOURCES["pj_elif_01"] = '''"""Deep elif chains whose arms hold break / continue / while / for."""


def pj_entry(v, ns=(1, 2, 3)):
    """Zero-arg-callable entry: six-arm elif chain, loop arms inside."""
    if v == 1:
        out = []
        for n in ns:
            if n > 1:
                break
            out.append(n)
    elif v == 2:
        out = []
        for n in ns:
            if n == 2:
                continue
            out.append(n)
    elif v == 3:
        out = 0
        while out < 3:
            out += 1
    elif v == 4:
        out = list(ns)
    elif v == 5:
        out = [n for n in ns if n]
    else:
        out = None
    return out


def pj_entry_nested(v):
    """Zero-arg-callable entry: elif inside elif (nested chain)."""
    if v > 0:
        if v > 10:
            return "big"
        elif v > 5:
            return "mid"
        elif v > 1:
            return "small"
        else:
            return "unit"
    elif v == 0:
        return "zero"
    return "neg"


def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    return pj_entry(1), pj_entry_nested(2)

def main():
    return pj_entry(1), pj_entry_nested(2)


if __name__ == "__main__":
    main()
'''

SOURCES["pj_elif_02"] = '''"""Elif chains whose arms hold try / match / raise / return."""


def pj_entry(v):
    """Zero-arg-callable entry: elif chain with try and match arms."""
    if v == 1:
        try:
            out = 1 / v
        except ZeroDivisionError:
            out = None
        finally:
            out = out or 0
    elif v == 2:
        match v:
            case 2:
                out = "two"
            case _:
                out = "other"
    elif v == 3:
        out = {"k": v}
    else:
        raise ValueError("unsupported")
    return out


def pj_entry_raise(v):
    """Zero-arg-callable entry: elif chain that re-raises in one arm."""
    if v < 0:
        raise ValueError(v)
    elif v == 0:
        return 0
    elif v < 10:
        return v * 2
    return v


def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    return pj_entry(2), pj_entry_raise(1)

def main():
    return pj_entry(2), pj_entry_raise(1)


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------- cluster 4 --
# StructuredAnalyzer._identify_with_structures (5 empty rules; the anchors are
# inside the multi-BEFORE_WITH merge branch).
SOURCES["pj_with_01"] = '''"""Multi-context and nested ``with`` shapes (sync).

Targets StructuredAnalyzer._identify_with_structures, whose anchor lines sit in
the branch that requires >=2 BEFORE_WITH instructions in one block with no
STORE_FAST/POP_TOP between them (i.e. a multi-item ``with``).
"""


class Ctx:
    def __init__(self, tag):
        self.tag = tag

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.tag


def pj_entry(a, b):
    """Zero-arg-callable entry: two-item with."""
    with Ctx(a) as first, Ctx(b) as second:
        out = (first.read(), second.read())
    return out


def pj_entry_three(a, b, c):
    """Zero-arg-callable entry: three-item with (longer BEFORE_WITH run)."""
    with Ctx(a) as x, Ctx(b) as y, Ctx(c) as z:
        out = x.read() + y.read() + z.read()
    return out


def pj_entry_nested(a, b):
    """Zero-arg-callable entry: nested with statements."""
    with Ctx(a) as outer:
        with Ctx(b) as inner:
            return outer.read(), inner.read()


def pj_entry_module_level(a, b):
    """Zero-arg-callable entry: with inside try/except/else."""
    try:
        with Ctx(a) as x, Ctx(b) as y:
            out = x.read(), y.read()
    except ValueError:
        out = ()
    else:
        out = out + ("else",)
    return out


def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    return (pj_entry(1, 2), pj_entry_three(1, 2, 3),
            pj_entry_nested(1, 2), pj_entry_module_level(1, 2))

def main():
    return pj_entry(1, 2), pj_entry_three(1, 2, 3), pj_entry_nested(1, 2)


if __name__ == "__main__":
    main()
'''

SOURCES["pj_with_02"] = '''"""Async multi-context ``with`` shapes.

Same anchor branch as pj_with_01 but on BEFORE_ASYNC_WITH paths (the anchor
line also accepts GET_AWAITABLE / SEND / YIELD_VALUE / RESUME).
"""


class ACtx:
    def __init__(self, tag):
        self.tag = tag

    async def __aenter__(self):
        return self.tag

    async def __aexit__(self, *exc):
        return False


async def pj_entry(a, b):
    """Zero-arg-callable entry: async two-item with."""
    async with ACtx(a) as first, ACtx(b) as second:
        out = (first, second)
    return out


async def pj_entry_await(a, b):
    """Zero-arg-callable entry: async with plus awaits inside the body."""
    async with ACtx(a) as x, ACtx(b) as y:
        left = await _one(x)
        right = await _one(y)
    return left, right


async def _one(v):
    return v


async def pj_entry_async_try(a):
    """Zero-arg-callable entry: async with inside try/finally."""
    try:
        async with ACtx(a) as x:
            return x
    finally:
        pass


async def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    return await pj_entry(1, 2), await pj_entry_await(1, 2)

def main():
    return pj_entry(1, 2), pj_entry_await(1, 2)


if __name__ == "__main__":
    main()
'''

# ---------------------------------------------------------------- cluster 5 --
# ObjectivePatchDetector._extract_test_pattern (4 empty rules; isinstance tests
# over ast.BoolOp / ast.Compare / ast.Attribute / ast.Call (and the same tests
# in core/cfg/patch_detector.py)).
SOURCES["pj_patchpat_01"] = '''"""Condition shapes a patch detector classifies as test patterns.

Targets ObjectivePatchDetector._extract_test_pattern (isinstance over
ast.Compare / ast.BoolOp / ast.Attribute / ast.Call) and the matching tests in
core/cfg/patch_detector.py.
"""


class Target:
    def __init__(self):
        self.attr = 1
        self.other = 0

    def method(self):
        return 2


def pj_entry(obj, other, fn):
    """Zero-arg-callable entry: attribute compare, boolop and call tests."""
    if obj.attr == 1:
        out = "cmp"
    elif obj.attr and other.other:
        out = "boolop"
    elif fn():
        out = "call"
    else:
        out = "none"
    return out, obj.method


def pj_entry_attr(obj):
    """Zero-arg-callable entry: attribute-valued tests only."""
    if obj.attr:
        return 1
    if not obj.other:
        return 2
    return 3


def pj_entry_compare(obj, other):
    """Zero-arg-callable entry: chained comparisons and identity tests."""
    if 0 < obj.attr < other.other:
        return "chain"
    if obj.attr is not None and obj.other is not None:
        return "identity"
    return "plain"


def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    t = Target()
    return pj_entry(t, t, t.method), pj_entry_attr(t), pj_entry_compare(t, t)

def main():
    t = Target()
    return pj_entry(t, t, t.method), pj_entry_attr(t), pj_entry_compare(t, t)


if __name__ == "__main__":
    main()
'''

SOURCES["pj_patchpat_02"] = '''"""Patch-shaped guards: attribute/call tests wrapped in equality arms."""


class Widget:
    def __init__(self):
        self.flag = True
        self.value = 3

    def enabled(self):
        return self.flag


def pj_entry(w, registry):
    """Zero-arg-callable entry: ``if`` arms over attribute and call tests."""
    if w.enabled():
        w.value = 4
    elif w.flag == 1:
        w.value = 5
    elif registry.get("k", 0) and w.value:
        w.value = 6
    return w.value


def pj_entry_nested(w):
    """Zero-arg-callable entry: nested attribute tests inside a boolop."""
    if (w.flag and w.value > 1) or (not w.flag and w.value == 0):
        return "mixed"
    if hasattr(w, "flag") and getattr(w, "value", 0):
        return "reflective"
    return "plain"


def main():
    return pj_entry(Widget(), {}), pj_entry_nested(Widget())


if __name__ == "__main__":
    main()
'''


def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    return pj_entry(Widget(), {}), pj_entry_nested(Widget())

def main():
    os.makedirs(OUT, exist_ok=True)
    written = []
    for name in sorted(SOURCES):
        path = os.path.join(OUT, name + ".py")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(SOURCES[name])
        written.append(path)
    print(json.dumps({"probes": len(written), "dir": OUT}, ensure_ascii=False))
    for path in written:
        print(" ", os.path.basename(path))


if __name__ == "__main__":
    main()
