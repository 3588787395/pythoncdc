# -*- coding: utf-8 -*-
"""Round 32: ptradeAccount.pyc 全函数字节码一致性验证。
用法（Python 3.11.7）：D:/Python/python.exe verify_ptrade_full.py
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
PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
OK_PY = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccountOK.py"


def load_code(p):
    with open(p, "rb") as f:
        f.read(16)
        return marshal.load(f)


def compile_ok(ok_py):
    cfile = py_compile.compile(ok_py, doraise=True, quiet=2)
    return load_code(cfile)


def walk(co, acc):
    acc.append(co.co_name or "<module>")
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, acc)
    return acc


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


import pycdc

src = pycdc.decompile_pyc(PYC, use_cfg=True)
with open(OK_PY, "w", encoding="utf-8") as f:
    f.write(src)

orig = load_code(PYC)
dec = compile_ok(OK_PY)
alln = [n for n in walk(orig, []) if n != "<module>"]

matched, mismatched = [], []
for name in alln:
    o = find(orig, name)
    d = find(dec, name)
    if o is None or d is None:
        mismatched.append((name, "MISSING in %s" % ("orig" if o is None else "dec")))
        continue
    if same_code(o, d):
        matched.append(name)
    else:
        oi, di = instrs(o), instrs(d)
        # 找第一个差异指令
        diff = None
        for a, b in zip(oi, di):
            if (a.opname, a.arg, a.argrepr) != (b.opname, b.arg, b.argrepr):
                diff = (a.opname, a.argrepr, b.opname, b.argrepr)
                break
        mismatched.append((name, "co_code/consts diff len=%d/%d first=%s" % (len(oi), len(di), diff)))

print("total=%d matched=%d mismatched=%d" % (len(alln), len(matched), len(mismatched)))
for name, reason in mismatched:
    print("  MISMATCH %s: %s" % (name, reason))
