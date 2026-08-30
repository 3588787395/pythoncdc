# -*- coding: utf-8 -*-
"""Round 32 回归：t_nested/t_paired/F_return_after_finally + ptradeAccount 目标函数。
用法（Python 3.11.7）：D:/Python/python.exe verify_regression.py
"""
import os
import sys
import types
import marshal
import py_compile

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

REPAIR = os.path.join(ROOT, ".trae", "specs", "region-based-pyc-decompile-iteration",
                      "rounds", "round_32", "repair_engineer")


def load_code(p):
    with open(p, "rb") as f:
        f.read(16)
        return marshal.load(f)


def compile_ok(ok_py):
    cfile = py_compile.compile(ok_py, doraise=True, quiet=2)
    return load_code(cfile)


def find(co, name):
    if (co.co_name or "<module>") == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find(c, name)
            if r:
                return r
    return None


def instrs(co):
    return [i for i in __import__("dis").get_instructions(co) if i.opname not in ("RESUME", "CACHE")]


def same_code(o, d):
    if len(o.co_code) != len(d.co_code) or o.co_code != d.co_code:
        return False
    if o.co_consts != d.co_consts:
        return False
    if o.co_names != d.co_names:
        return False
    if o.co_varnames != d.co_varnames:
        return False
    return True


def check(pyc, label, funcs):
    import pycdc
    ok_py = os.path.join(REPAIR, label + "_regr.py")
    try:
        src = pycdc.decompile_pyc(pyc, use_cfg=True)
        with open(ok_py, "w", encoding="utf-8") as f:
            f.write(src)
        orig = load_code(pyc)
        dec = compile_ok(ok_py)
    except Exception as e:
        print("[%s] ERROR %r" % (label, e))
        return
    ok = 0
    for name in funcs:
        o = find(orig, name)
        d = find(dec, name)
        if o is None or d is None:
            print("[%s] %s: MISSING" % (label, name))
            continue
        if same_code(o, d):
            ok += 1
        else:
            oi, di = instrs(o), instrs(d)
            print("[%s] %s: MISMATCH orig=%d decomp=%d" % (label, name, len(oi), len(di)))
    print("[%s] matched=%d/%d" % (label, ok, len(funcs)))


check(os.path.join(REPAIR, "t_nested.pyc"), "t_nested", ["nested"])
check(os.path.join(REPAIR, "t_paired.pyc"), "t_paired", ["paired"])
check(os.path.join(REPAIR, "..", "test_engineer", "variant_work", "F_return_after_finally.pyc"),
      "F_return_after_finally", ["f"])
check(r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc",
      "ptradeAccount_targets", ["order_response_order_update", "trade_response_order_update"])
