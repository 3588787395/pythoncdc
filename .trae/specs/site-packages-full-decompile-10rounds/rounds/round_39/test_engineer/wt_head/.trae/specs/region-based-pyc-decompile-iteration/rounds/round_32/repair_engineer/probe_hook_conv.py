# -*- coding: utf-8 -*-
"""Round 32: 定位 frozenset -> tuple 转换点（hook converter.convert 返回值）。
用法（Python 3.11.7）：D:/Python/python.exe probe_hook_conv.py
"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

import core.cfg.ast_converter as ac
import core.cfg.code_generator as cg

_orig_conv = ac.CFGASTConverter.convert
_conv_results = []


def _patched_conv(self, ast_dict):
    node = _orig_conv(self, ast_dict)
    # 遍历找 ASTConstant 值为 frozenset/tuple(5,6) 的节点
    found = []

    def walk(n, path, depth=0):
        if n is None or depth > 60:
            return
        tn = type(n).__name__
        if tn == "ASTConstant":
            v = getattr(n, "value", None)
            if isinstance(v, frozenset) and v == frozenset({5, 6}):
                found.append(("FROZENSET", path, repr(v)))
            elif isinstance(v, tuple) and v == (5, 6):
                found.append(("TUPLE", path, repr(v)))
        attrs = set()
        for klass in type(n).__mro__:
            attrs.update(getattr(klass, "__slots__", ()))
        if hasattr(n, "__dict__"):
            attrs.update(n.__dict__.keys())
        for a in attrs:
            if a.startswith("_"):
                continue
            try:
                v = getattr(n, a)
            except Exception:
                continue
            if isinstance(v, list):
                for i, item in enumerate(v):
                    walk(item, path + "." + a + "[%d]" % i, depth + 1)
            else:
                walk(v, path + "." + a, depth + 1)

    walk(node, "$")
    _conv_results.append(found)
    return node


ac.CFGASTConverter.convert = _patched_conv

import pycdc

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
src = pycdc.decompile_pyc(PYC, use_cfg=True)

print("=== converter.convert 返回树中的 frozenset/tuple(5,6) ===")
for r in _conv_results:
    for item in r:
        print(item)
print("total convert calls:", len(_conv_results))

print("\n=== target line ===")
for i, line in enumerate(src.splitlines()):
    if "in (5, 6)" in line or "in {5, 6}" in line:
        print("line %d: %r" % (i, line))
