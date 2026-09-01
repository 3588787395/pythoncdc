# -*- coding: utf-8 -*-
"""Round 32: PtradeAccount 类体字节码 diff 定位。
用法（Python 3.11.7）：D:/Python/python.exe probe_diff3.py
"""
import os
import sys
import types
import marshal
import py_compile
import dis

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
OK_PY = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccountOK.py"


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


orig = load_code(PYC)
dec = compile_ok(OK_PY)
o = find(orig, "PtradeAccount")
d = find(dec, "PtradeAccount")

oi = [i for i in dis.get_instructions(o) if i.opname not in ("RESUME", "CACHE")]
di = [i for i in dis.get_instructions(d) if i.opname not in ("RESUME", "CACHE")]
print("orig len=%d instrs=%d ; dec len=%d instrs=%d" % (len(o.co_code), len(oi), len(d.co_code), len(di)))

print("\n=== 指令级 diff ===")
i = j = 0
shown = 0
while i < len(oi) and j < len(di) and shown < 20:
    a, b = oi[i], di[j]
    if (a.opname, a.arg, a.argrepr) != (b.opname, b.arg, b.argrepr):
        print("orig[%d] %-5d %-32s %s" % (i, a.offset, a.opname, a.argrepr))
        print("dec [%d] %-5d %-32s %s" % (j, b.offset, b.opname, b.argrepr))
        print("---")
        shown += 1
        i += 1
        j += 1
    else:
        i += 1
        j += 1

print("\n=== orig 全部 ===")
for x in oi:
    print("  %-5d %-32s %s" % (x.offset, x.opname, x.argrepr))
