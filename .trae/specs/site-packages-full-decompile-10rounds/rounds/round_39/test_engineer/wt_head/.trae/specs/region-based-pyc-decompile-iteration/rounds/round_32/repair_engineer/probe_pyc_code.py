# -*- coding: utf-8 -*-
"""Round 32: 检查 PycDecompiler.to_python_code 后 trade_response_order_update 的 co_consts。
用法（Python 3.11.7）：D:/Python/python.exe probe_pyc_code.py
"""
import os
import sys
import types

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from pycdc import PycDecompiler

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"

decompiler = PycDecompiler()
ok = decompiler.load_file(PYC)
print("load_file:", ok)

mc = decompiler.module.code
if hasattr(mc, "get"):
    co = mc.get()
else:
    co = mc
print("code_obj type:", type(co).__name__)
if hasattr(co, "to_python_code"):
    actual = co.to_python_code()
    print("actual type:", type(actual).__name__)

    def find(co2, name):
        if (co2.co_name or "<module>") == name:
            return co2
        for c in co2.co_consts:
            if isinstance(c, types.CodeType):
                r = find(c, name)
                if r:
                    return r
        return None

    fco = find(actual, "trade_response_order_update")
    print("found func:", fco is not None)
    if fco:
        print("func consts:")
        for c in fco.co_consts:
            print("   type=%s repr=%r" % (type(c).__name__, repr(c)[:80]))
else:
    print("no to_python_code; code_obj consts:")
    for c in co.co_consts:
        print("   type=%s repr=%r" % (type(c).__name__, repr(c)[:80]))
