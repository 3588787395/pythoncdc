# -*- coding: utf-8 -*-
"""Round 32: hook generate_ast_v2，检查其生成的 ast_dict 中 Compare 的 comparator 形态。
用法（Python 3.11.7）：D:/Python/python.exe probe_hook_v2.py
"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

import core.cfg.ast_generator_v2 as v2mod

_orig_v2 = v2mod.generate_ast_v2
_v2_hits = []


def _patched_v2(cfg, recursive=True):
    d = _orig_v2(cfg, recursive=recursive)
    # 遍历 ast_dict 找含 5/6 的 Compare 或 Constant
    hits = []

    def walk(x, path):
        if isinstance(x, dict):
            t = x.get("type")
            if t == "Compare":
                comps = x.get("comparators", [])
                for i, c in enumerate(comps):
                    if isinstance(c, dict):
                        if c.get("type") == "Constant":
                            v = c.get("value")
                            if isinstance(v, (frozenset, tuple, set)) and "5" in str(v):
                                hits.append(("COMPARE", path + ".comparators[%d]" % i, c.get("type"), type(v).__name__, repr(v)))
                        elif c.get("type") in ("Tuple", "Set", "List"):
                            hits.append(("COMPARE", path + ".comparators[%d]" % i, c.get("type"), "node", repr(c)[:120]))
            elif t == "Constant":
                v = x.get("value")
                if isinstance(v, (frozenset, tuple, set)) and "5" in str(v):
                    hits.append(("CONST", path, type(v).__name__, repr(v)))
            for k, v in x.items():
                if k == "type":
                    continue
                walk(v, path + "." + k)
        elif isinstance(x, list):
            for i, item in enumerate(x):
                walk(item, path + "[%d]" % i)

    walk(d, "$")
    if hits:
        _v2_hits.append((cfg.name, hits))
    return d


v2mod.generate_ast_v2 = _patched_v2

import pycdc

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
src = pycdc.decompile_pyc(PYC, use_cfg=True)

print("=== generate_ast_v2 输出中含 5/6 的结果 ===")
for name, hits in _v2_hits:
    print("func:", name)
    for h in hits:
        print("   ", h)
print("total v2 calls:", len(_v2_hits))

print("\n=== target line ===")
for i, line in enumerate(src.splitlines()):
    if "in (5, 6)" in line or "in {5, 6}" in line:
        print("line %d: %r" % (i, line))
