# -*- coding: utf-8 -*-
"""Round 32: 正确定位 frozenset -> tuple 转换点（hook converter.convert，正确遍历 slots）。
用法（Python 3.11.7）：D:/Python/python.exe probe_hook_conv2.py
"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

import core.cfg.ast_converter as ac

_orig_conv = ac.CFGASTConverter.convert
_conv_results = []
_SKIP = {"_parent", "_node_id", "_processed", "_type", "_line_number"}


def _walk(n, path, found, depth=0, visited=None):
    if n is None or depth > 60:
        return
    if visited is None:
        visited = set()
    if id(n) in visited:
        return
    visited.add(id(n))
    tn = type(n).__name__
    if tn == "ASTConstant":
        v = getattr(n, "value", None)
        if isinstance(v, frozenset) and v == frozenset({5, 6}):
            found.append(("FROZENSET", path, repr(v)))
        elif isinstance(v, tuple) and v == (5, 6):
            found.append(("TUPLE", path, repr(v)))
        elif isinstance(v, (tuple, frozenset, set, list)) and "5" in str(v):
            found.append(("OTHER-" + type(v).__name__, path, repr(v)))
    attrs = set()
    for klass in type(n).__mro__:
        attrs.update(getattr(klass, "__slots__", ()))
    if hasattr(n, "__dict__"):
        attrs.update(n.__dict__.keys())
    for a in attrs:
        if a in _SKIP:
            continue
        try:
            v = getattr(n, a)
        except Exception:
            continue
        if isinstance(v, list):
            for i, item in enumerate(v):
                _walk(item, path + "." + a + "[%d]" % i, found, depth + 1, visited)
        else:
            _walk(v, path + "." + a, found, depth + 1, visited)


def _patched_conv(self, ast_dict):
    node = _orig_conv(self, ast_dict)
    found = []
    _walk(node, "$", found)
    if found:
        _conv_results.append((ast_dict.get("type") if isinstance(ast_dict, dict) else type(ast_dict).__name__, found))
    return node


ac.CFGASTConverter.convert = _patched_conv

import pycdc

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
src = pycdc.decompile_pyc(PYC, use_cfg=True)

print("=== convert 调用中含 frozenset/tuple(5,6) 的结果 ===")
for root_type, found in _conv_results:
    print("root:", root_type)
    for f in found:
        print("   ", f)
print("total convert calls:", len(_conv_results))

print("\n=== target line ===")
for i, line in enumerate(src.splitlines()):
    if "in (5, 6)" in line or "in {5, 6}" in line:
        print("line %d: %r" % (i, line))
