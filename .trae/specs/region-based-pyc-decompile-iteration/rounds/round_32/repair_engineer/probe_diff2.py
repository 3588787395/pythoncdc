# -*- coding: utf-8 -*-
"""Round 32: 对比 stock_order_response_transform / PtradeAccount 的原始与反编译字节码。
用法（Python 3.11.7）：D:/Python/python.exe probe_diff2.py
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

for name in ("stock_order_response_transform", "PtradeAccount"):
    o = find(orig, name)
    d = find(dec, name)
    print("=" * 70)
    print("FUNC:", name, "orig_len=%d dec_len=%d" % (len(o.co_code), len(d.co_code)))
    oi = [i for i in dis.get_instructions(o) if i.opname not in ("RESUME", "CACHE")]
    di = [i for i in dis.get_instructions(d) if i.opname not in ("RESUME", "CACHE")]
    # 打印完整指令对比
    print("--- orig ---")
    for i in oi:
        print("  %-6d %-32s %s" % (i.offset, i.opname, i.argrepr))
    print("--- dec ---")
    for i in di:
        print("  %-6d %-32s %s" % (i.offset, i.opname, i.argrepr))
