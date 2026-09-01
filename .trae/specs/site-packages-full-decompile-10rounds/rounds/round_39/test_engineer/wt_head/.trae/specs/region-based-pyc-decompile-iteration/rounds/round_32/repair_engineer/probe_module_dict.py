# -*- coding: utf-8 -*-
"""Round 32: 整模块路径——检查 RegionASTGenerator(module) 生成 ast_dict 中
trade_response_order_update 的 status in <5,6> comparator 形态。
用法（Python 3.11.7）：D:/Python/python.exe probe_module_dict.py
"""
import os
import sys
import types
import marshal

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator


def load_code(p):
    with open(p, "rb") as f:
        f.read(16)
        return marshal.load(f)


PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
co = load_code(PYC)  # module code
print("module name:", co.co_name)

cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=co)
ast_dict = gen.generate()
print("root type:", ast_dict.get("type") if isinstance(ast_dict, dict) else type(ast_dict).__name__)

hits = []


def walk(d, path):
    if isinstance(d, dict):
        t = d.get("type")
        if t == "Constant":
            v = d.get("value")
            if isinstance(v, frozenset) and v == frozenset({5, 6}):
                hits.append(("CONST-FROZENSET", path, repr(v)))
            elif isinstance(v, tuple) and v == (5, 6):
                hits.append(("CONST-TUPLE", path, repr(v)))
            elif isinstance(v, (set, list)) and "5" in str(v):
                hits.append(("CONST-" + type(v).__name__, path, repr(v)))
        elif t == "Compare":
            for i, c in enumerate(d.get("comparators", [])):
                if isinstance(c, dict):
                    ct = c.get("type")
                    cv = c.get("value")
                    if isinstance(cv, (frozenset, tuple, set, list)) and "5" in str(cv):
                        hits.append(("COMPARE", path + ".comparators[%d]" % i, ct, type(cv).__name__, repr(cv)))
                    elif ct in ("Tuple", "Set", "List"):
                        hits.append(("COMPARE-NODE", path + ".comparators[%d]" % i, ct, repr(c)[:150]))
        for k, v in d.items():
            if k == "type":
                continue
            walk(v, path + "." + k)
    elif isinstance(d, list):
        for i, item in enumerate(d):
            walk(item, path + "[%d]" % i)


walk(ast_dict, "$")
print("\n=== hits (%d) ===" % len(hits))
for h in hits[:30]:
    print(h)
