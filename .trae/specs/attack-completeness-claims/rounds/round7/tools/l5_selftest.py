"""L5: validate the feature detectors themselves.

An evidence-layer audit that rests on unvalidated detectors would be exactly the
kind of self-certifying evidence this round attacks.  Every detector is checked
against a synthetic sample whose ground truth is known by construction, plus a
negative control that must NOT trigger any optional detector.

Output: logs/l5_selftest.json
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import l5_features as F  # noqa: E402

# (name, source, expected-present, expected-absent)
SAMPLES = [
    ("fstring", 'def f(x):\n    return f"{x}!"\n', ["fstring"], []),
    ("annotation",
     'def f(x: int) -> str:\n    y: int = x\n    return str(y)\n',
     ["annotation"], []),
    ("annotation_module", 'v: int = 1\n', ["annotation"], []),
    ("dataclass",
     'import dataclasses\n@dataclasses.dataclass\nclass C:\n    a: int = 1\n',
     ["dataclass"], []),
    ("async_def", 'async def f():\n    return 1\n', ["async_def"], []),
    ("except_star",
     'try:\n    pass\nexcept* ValueError as eg:\n    print(eg)\n',
     ["except_star", "try_except"], []),
    ("closure",
     'def outer():\n    x = 1\n    def inner():\n        return x\n    return inner\n',
     ["closure", "nested_def"], []),
    ("decorator_chain",
     'def d1(f):\n    return f\ndef d2(f):\n    return f\n@d1\n@d2\ndef g():\n    return 1\n',
     ["decorator", "decorator_chain"], []),
    ("generator", 'def g():\n    yield 1\n', ["generator"], []),
    ("lambda", 'f = lambda x: x + 1\n', ["lambda"], []),
    ("match_stmt",
     'def f(v):\n    match v:\n        case [1,2]:\n            return 1\n        case _:\n            return 2\n',
     ["match_stmt"], []),
    ("except_multi_type",
     'def f():\n    try:\n        x = 1\n    except (ValueError, TypeError):\n        x = 2\n    return x\n',
     ["try_except"], ["except_star"]),
    ("match_literal_only",
     'def f(v):\n    match v:\n        case 1:\n            return "a"\n        case _:\n            return "b"\n',
     [], []),   # literal-only match: bytecode-invisible (documented limit)
    ("comprehension", 'r = [i for i in range(3)]\n', ["comprehension"], []),
    ("try_except",
     'def f():\n    try:\n        x = 1\n    except ValueError:\n        x = 2\n    return x\n',
     ["try_except"], []),
    ("try_finally",
     'def f():\n    try:\n        x = 1\n    finally:\n        print("c")\n    return x\n',
     ["try_finally"], ["try_except"]),
    ("with_stmt",
     'def f(p):\n    with open(p) as fh:\n        return fh.read()\n',
     ["with_stmt"], []),
    ("global_stmt",
     'v = 0\ndef f():\n    global v\n    v = 1\n', ["global_stmt"], []),
    ("nested_def",
     'def outer():\n    def inner():\n        return 1\n    return inner\n',
     ["nested_def"], []),
    ("assert_stmt", 'def f(x):\n    assert x, "bad"\n', ["assert_stmt"], []),
    ("del_stmt", 'def f():\n    x = 1\n    del x\n', ["del_stmt"], []),
    ("slice_step", 'def f(s):\n    return s[::2]\n', ["slice_step"], []),
    ("star_call", 'def f(a):\n    return g(*a)\n', ["star_call"], []),
    ("walrus", 'def f(a):\n    if (n := len(a)) > 1:\n        return n\n    return 0\n',
     ["walrus"], []),
    ("async_for",
     'async def f(g):\n    async for x in g:\n        print(x)\n',
     ["async_for", "async_def"], []),
    ("yield_from", 'def f(g):\n    yield from g\n', ["yield_from", "generator"], []),
    ("boolop_chain", 'def f(a, b, c):\n    return a and b and c\n',
     ["boolop_chain"], []),
    ("pep604", 'def f(x: int | str) -> int | None:\n    return None\n',
     [], []),   # bytecode-invisible; source-only check below
    ("chain_compare", 'def f(a, b, c):\n    return a < b < c\n', [], []),
    ("ifexp", 'def f(a, b):\n    return a if b else 0\n', [], []),
    ("NEG_control",
     'def plain(a, b):\n    total = a + b\n    return total\n',
     [], ["fstring", "annotation", "dataclass", "async_def", "except_star",
          "closure", "decorator", "decorator_chain", "generator", "lambda",
          "match_stmt", "comprehension", "try_except", "with_stmt",
          "global_stmt", "nested_def", "assert_stmt", "del_stmt",
          "slice_step", "star_call", "walrus", "async_for", "yield_from",
          "boolop_chain"]),
]

# forms whose ground truth is only decidable on the source plane
SOURCE_ONLY_EXPECT = {
    "pep604": ("pep604_union", True),
    "chain_compare": ("chain_compare", True),
    "ifexp": ("ifexp", True),
}


def main() -> int:
    rows = []
    failures = []
    tmp = tempfile.mkdtemp(prefix="l5_selftest_")
    try:
        from xdis.bytecode import parse_exception_table as xdis_parse
        have_xdis = True
    except Exception:
        have_xdis = False
    for name, src, exp_present, exp_absent in SAMPLES:
        py = os.path.join(tmp, name + ".py")
        with open(py, "w", encoding="utf-8") as fh:
            fh.write(src)
        import py_compile
        pyc = os.path.join(tmp, name + ".pyc")
        py_compile.compile(py, cfile=pyc, doraise=True, optimize=0)
        code = F.load_pyc_code(pyc)
        bf = F.bytecode_features(code)
        sf = F.source_features(src)
        bfeat = bf["features"]
        sfeat = sf["features"]
        row = {"name": name, "bytecode": bfeat, "source": sfeat,
               "bytecode_scale": {k: v for k, v in bf.items() if k != "features"},
               "source_scale": {k: v for k, v in sf.items() if k != "features"}}
        ok = True
        # cross-check the exception-table decoding against the judge's own
        # parser (the pylingual ruler uses xdis.bytecode.parse_exception_table)
        if have_xdis:
            for co in F.iter_code(code):
                tbl = getattr(co, "co_exceptiontable", b"")
                if not tbl:
                    continue
                mine = [(s, e, t, d) for (s, e, t, d) in F._exc_entries(co)]
                theirs = [(x.start, x.end, x.target, x.depth)
                          for x in xdis_parse(tbl)]
                if mine != theirs:
                    ok = False
                    failures.append("%s: exception-table decode differs from xdis "
                                    "(judge parser): %r vs %r"
                                    % (name, mine, theirs))
        for form in exp_present:
            if bfeat.get(form, 0) <= 0:
                ok = False
                failures.append("%s: bytecode form %r not detected" % (name, form))
        for form in exp_absent:
            if bfeat.get(form, 0) != 0:
                ok = False
                failures.append("%s: bytecode form %r falsely detected (%d)"
                                % (name, form, bfeat[form]))
        # source-plane ground truth for source-only forms
        if name in SOURCE_ONLY_EXPECT:
            form, want = SOURCE_ONLY_EXPECT[name]
            got = sfeat.get(form, 0) > 0
            if got != want:
                ok = False
                failures.append("%s: source form %r expected %s got %s"
                                % (name, form, want, got))
        # cross-plane agreement on the forms both planes can see
        for form in F.BYTECODE_DECIDABLE:
            if form in F.SOURCE_PREFERRED:
                continue
            if (bfeat.get(form, 0) > 0) != (sfeat.get(form, 0) > 0):
                ok = False
                failures.append("%s: plane disagreement on %r (bytecode=%d source=%d)"
                                % (name, form, bfeat.get(form, 0), sfeat.get(form, 0)))
        row["ok"] = ok
        rows.append(row)

    payload = {
        "tool": "l5_selftest.py",
        "python": sys.version,
        "n_samples": len(rows),
        "n_failures": len(failures),
        "failures": failures,
        "rows": rows,
    }
    out = os.path.join(ROUND, "logs", "l5_selftest.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    print("selftest samples:", len(rows), "failures:", len(failures))
    for f in failures:
        print("  FAIL", f)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
