# -*- coding: utf-8 -*-
"""Round 32: 打印 stock_order_response_transform orig 字节码 480-800 区间。
用法（Python 3.11.7）：D:/Python/python.exe probe_diff2_mid.py
"""
import os
import sys
import types
import marshal
import dis

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"


def load_code(p):
    with open(p, "rb") as f:
        f.read(16)
        return marshal.load(f)


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
o = find(orig, "stock_order_response_transform")
oi = [i for i in dis.get_instructions(o) if i.opname not in ("RESUME", "CACHE")]
for x in oi:
    if 470 <= x.offset <= 800:
        print("  %-5d %-32s %s" % (x.offset, x.opname, x.argrepr))
