# -*- coding: utf-8 -*-
"""Round 32: 检查 generate_ast_v2 生成的 AST dict 中 comparator 形态。
用法（Python 3.11.7）：D:/Python/python.exe probe_v2_fs.py
"""
import os
import sys
import types
import marshal

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.cfg.cfg_builder import build_cfg
from core.cfg.ast_generator_v2 import generate_ast_v2


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


PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"
FNAME = "trade_response_order_update"

co = load_code(PYC)
fco = find(co, FNAME)

cfg = build_cfg(fco, fco.co_name)
ast_dict = generate_ast_v2(cfg)
print("v2 ast_dict root type:", ast_dict.get("type") if isinstance(ast_dict, dict) else type(ast_dict).__name__)

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
        elif t == "Set":
            hits.append(("SET-NODE", path, repr(d)))
        elif t == "Tuple":
            hits.append(("TUPLE-NODE", path, repr(d)))
        elif t == "Compare":
            # 打印 compare 结构
            hits.append(("COMPARE", path, repr(d)[:300]))
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
