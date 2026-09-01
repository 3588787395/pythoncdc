# -*- coding: utf-8 -*-
"""Round 32: hook 真实 decompile_pyc 路径，记录 _generate_constant 收到的 frozenset/tuple。
用法（Python 3.11.7）：D:/Python/python.exe probe_hook_gen.py
"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

import core.cfg.code_generator as cg

_orig = cg.CodeGenerator._generate_constant
_calls = []


def _patched(self, node):
    v = node.value
    if isinstance(v, (frozenset, set, tuple, list)) and ("5" in str(v)):
        _calls.append((type(v).__name__, repr(v), type(node).__name__))
    return _orig(self, node)


cg.CodeGenerator._generate_constant = _patched

import pycdc

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
src = pycdc.decompile_pyc(PYC, use_cfg=True)
print("=== _generate_constant calls with container (5/6) ===")
for c in _calls[:30]:
    print(c)
print("total calls:", len(_calls))

print("\n=== target line ===")
for i, line in enumerate(src.splitlines()):
    if "in (5, 6)" in line or "in {5, 6}" in line:
        print("line %d: %r" % (i, line))
