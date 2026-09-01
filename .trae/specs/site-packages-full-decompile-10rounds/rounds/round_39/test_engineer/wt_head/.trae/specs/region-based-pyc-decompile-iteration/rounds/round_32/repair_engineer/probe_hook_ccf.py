# -*- coding: utf-8 -*-
"""Round 32: hook _convert_compare_full，检查真实路径中 comparator 的转换时刻。
用法（Python 3.11.7）：D:/Python/python.exe probe_hook_ccf.py
"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

import core.cfg.ast_converter as ac

_orig_ccf = ac.CFGASTConverter._convert_compare_full
_hits = []


def _patched_ccf(self, expr_dict):
    # 检查入参 comparators 中是否含 frozenset/tuple
    comps = expr_dict.get("comparators", [])
    in_types = []
    for c in comps:
        if isinstance(c, dict):
            v = c.get("value")
            in_types.append((c.get("type"), type(v).__name__ if v is not None else "None", repr(v)[:60]))
        else:
            in_types.append(("RAW", type(c).__name__, repr(c)[:60]))
    result = _orig_ccf(self, expr_dict)
    # 检查返回值 comparator 类型
    out_types = []
    if result is not None and type(result).__name__ == "ASTCompare":
        for c in result.comparators:
            v = getattr(c, "value", "?")
            out_types.append((type(c).__name__, type(v).__name__, repr(v)[:60]))
    flag = "5" in str(in_types) or "5" in str(out_types)
    if flag:
        _hits.append((in_types, out_types))
    return result


ac.CFGASTConverter._convert_compare_full = _patched_ccf

import pycdc

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
src = pycdc.decompile_pyc(PYC, use_cfg=True)

print("=== _convert_compare_full 调用中含 5/6 的 (入参comparators, 返回comparators) ===")
for ins, outs in _hits[:10]:
    print("IN :", ins)
    print("OUT:", outs)
    print("---")
print("total ccf calls:", len(_hits))
