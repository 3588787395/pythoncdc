# -*- coding: utf-8 -*-
"""Round 32: 检查真实 ast_dict 中 status in frozenset 的 comparator 形态。
用法（Python 3.11.7）：D:/Python/python.exe probe_astdict_fs.py
"""
import os
import sys
import types
import marshal

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator


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
print("target func found:", fco is not None, fco.co_name if fco else None)

cfg = build_cfg(fco)
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()

# 遍历 ast_dict，找出包含 5/6 的容器字面量或 frozenset 常量
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
        for k, v in d.items():
            if k == "type":
                continue
            walk(v, path + "." + k)
    elif isinstance(d, list):
        for i, item in enumerate(d):
            walk(item, path + "[%d]" % i)


walk(ast_dict, "$")
print("\n=== hits (%d) ===" % len(hits))
for h in hits[:20]:
    print(h)

# 若没找到（可能被转成其它形态），打印所有含 5 的节点
if not hits:
    print("\n=== no direct hits; dump nodes containing value 5 ===")
    def walk2(d, path):
        if isinstance(d, dict):
            if d.get("value") == 5:
                print(path, "->", repr(d)[:200])
            for k, v in d.items():
                walk2(v, path + "." + k)
        elif isinstance(d, list):
            for i, item in enumerate(d):
                walk2(item, path + "[%d]" % i)
    walk2(ast_dict, "$")
