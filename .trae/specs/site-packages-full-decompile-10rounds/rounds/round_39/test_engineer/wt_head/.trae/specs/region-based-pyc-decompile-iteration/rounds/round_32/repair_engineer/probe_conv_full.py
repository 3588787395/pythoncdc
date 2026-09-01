# -*- coding: utf-8 -*-
"""Round 32: 完整真实路径 hook，检查 converter.convert(ast_dict) 后 ASTCompare 的 comparators 类型。
用法（Python 3.11.7）：D:/Python/python.exe probe_conv_full.py
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

cfg = build_cfg(fco)
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
print("py_ast root:", type(py_ast).__name__)

# 安全遍历 ASTNode 树找 ASTCompare，打印 comparators 类型
compares = []
visited = set()


def walk(n, path, depth=0):
    if n is None or depth > 40:
        return
    if id(n) in visited:
        return
    visited.add(id(n))
    name = type(n).__name__
    if name == "ASTCompare":
        try:
            comps = [type(c).__name__ + ":" + repr(getattr(c, "value", "?")) for c in n.comparators]
        except Exception as e:
            comps = ["ERR %r" % e]
        compares.append((path, comps))
    # 遍历所有已知子节点属性（slots + __dict__）
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


walk(py_ast, "$")
print("\n=== ASTCompare nodes (%d) ===" % len(compares))
for p, c in compares:
    if any("frozenset" in str(x) or "(5, 6)" in str(x) or "{5, 6}" in str(x) for x in c) or "5" in str(c):
        print(p, c)

# 生成源码，定位 status in 行
gen2 = CFGCodeGenerator()
src = gen2.generate(py_ast)
print("\n=== status in line ===")
for i, line in enumerate(src.splitlines()):
    if "in (5, 6)" in line or "in {5, 6}" in line:
        print("line %d: %r" % (i, line))
