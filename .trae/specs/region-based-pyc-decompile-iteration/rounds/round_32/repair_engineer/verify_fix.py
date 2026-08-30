# -*- coding: utf-8 -*-
"""Round 32 修复验证：F_return_after_finally 最小复现 + ptradeAccount 目标。
用法（Python 3.11.7）：D:/Python/python.exe verify_fix.py
"""
import os
import sys
import marshal
import types
import py_compile

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

W = os.path.join(ROOT, ".trae", "specs", "region-based-pyc-decompile-iteration",
                 "rounds", "round_32", "test_engineer", "variant_work")
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
    if len(o.co_code) != len(d.co_code):
        return False
    if o.co_code != d.co_code:
        return False
    if o.co_consts != d.co_consts:
        return False
    if o.co_names != d.co_names:
        return False
    if o.co_varnames != d.co_varnames:
        return False
    return True


def check_file(pyc, label, funcs=None):
    import pycdc
    ok_py = os.path.join(REPAIR, label + "OK_check.py")
    try:
        src = pycdc.decompile_pyc(pyc, use_cfg=True)
        with open(ok_py, "w", encoding="utf-8") as f:
            f.write(src)
        orig = load_code(pyc)
        dec = compile_ok(ok_py)
    except Exception as e:
        print("[%s] ERROR %r" % (label, e))
        return
    names = [c.co_name for c in [orig] ]
    def walk(co, acc):
        acc.append(co.co_name or "<module>")
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                walk(c, acc)
        return acc
    alln = walk(orig, [])
    if funcs is None:
        funcs = [n for n in alln if n != "<module>"]
    ok = 0
    for name in funcs:
        o = find(orig, name)
        d = find(dec, name)
        if o is None or d is None:
            print("[%s] %s: MISSING (%s/%s)" % (label, name, "orig" if o is None else "dec"))
            continue
        if same_code(o, d):
            ok += 1
        else:
            oi, di = instrs(o), instrs(d)
            print("[%s] %s: MISMATCH orig=%d decomp=%d first_diff=%s vs %s" % (
                label, name, len(oi), len(di),
                (oi[0].opname, oi[0].argrepr) if oi else None,
                (di[0].opname, di[0].argrepr) if di else None))
    print("[%s] total funcs checked=%d matched=%d" % (label, len(funcs), ok))


# 1. 最小复现
check_file(os.path.join(W, "F_return_after_finally.pyc"), "F_return_after_finally",
           funcs=["f"])

# 2. 目标 pyc：order_response_order_update / trade_response_order_update
check_file(r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc",
           "ptradeAccount",
           funcs=["order_response_order_update", "trade_response_order_update"])
