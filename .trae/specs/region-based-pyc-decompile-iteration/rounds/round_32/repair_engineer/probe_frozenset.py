# -*- coding: utf-8 -*-
"""Round 32: 追踪 trade_response_order_update 的 frozenset 渲染路径。
用法（Python 3.11.7）：D:/Python/python.exe probe_frozenset.py
"""
import os
import sys
import types
import marshal

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

import pycdc


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

# 1) 真实反编译输出
src = pycdc.decompile_pyc(PYC, use_cfg=True)
print("=== decompiled source contains: ===")
for i, line in enumerate(src.splitlines()):
    if "in (5, 6)" in line or "in {5, 6}" in line or "status" in line and "in" in line:
        print("line %d: %r" % (i, line))

# 2) 定位 AST dict 中 comparator 的类型
co = load_code(PYC)
fco = find(co, FNAME)
print("\n=== orig code consts: ===")
for c in fco.co_consts:
    if isinstance(c, frozenset):
        print("  frozenset const:", c)

# 3) 检查 decompile_pyc 内部生成的 AST（通过 monkey-patch CodeGenerator）
#    先看看 pycdc.decompile_pyc 的实现，找到 AST dict 的生成点
import inspect
print("\n=== decompile_pyc signature ===")
try:
    print(inspect.getsource(pycdc.decompile_pyc))
except Exception as e:
    print("getsource failed:", e)

# 4) 直接走 converter 转换路径：手动构造与真实一致的最小 AST dict
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CodeGenerator

test_dict = {
    "type": "If",
    "test": {
        "type": "Compare",
        "left": {"type": "Name", "id": "status"},
        "ops": ["in"],
        "comparators": [
            {"type": "Constant", "value": frozenset({5, 6})}
        ],
    },
    "body": [{"type": "Pass"}],
    "orelse": [],
}

conv = CFGASTConverter()
node = conv.convert(test_dict)
print("\n=== converter.convert result ===")
print("node type:", type(node).__name__)
# 遍历找 ASTCompare
found = []


def walk(n):
    if n is None:
        return
    if type(n).__name__ == "ASTCompare":
        found.append(n)
    # 通过 __dict__ 或已知 slots 访问子节点
    for attr in ("_test", "_body", "_left", "_right", "_comparators", "_nodes", "_target", "_value", "_items"):
        try:
            v = getattr(n, attr)
        except Exception:
            continue
        if isinstance(v, list):
            for item in v:
                walk(item)
        else:
            walk(v)


walk(node)
print("ASTCompare found:", len(found))
for cmp in found:
    print("  comparators types:", [type(c).__name__ for c in cmp.comparators])
    print("  comparator0 value:", repr(getattr(cmp.comparators[0], "value", None)) if cmp.comparators else None)

# 5) 直接生成
gen = CodeGenerator()
out = gen.generate(test_dict)
print("\n=== direct generate(manual dict) ===")
print(out)
