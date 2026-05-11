import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator
import json

tf = 'test_e11_loop_with_try.py'
with open(tf) as f:
    source = f.read()

code = compile(source, tf, 'exec')
func_code = code.co_consts[0]

cfg = build_cfg(func_code)
gen = RegionASTGenerator(cfg)
ast_dict = gen.generate()

print("=== AST Dict (For node) ===")
for node in ast_dict.get('body', []):
    if node.get('type') == 'For':
        print(json.dumps(node, indent=2, default=str))

# Also check: does "else: return s" vs "return s" after loop produce same bytecode?
print("\n=== Bytecode comparison: else: return s vs return s ===")
src1 = """
def test():
    s = 0
    for i in range(3):
        try:
            s += 10 // (i + 1)
        except ZeroDivisionError:
            s -= 1
    else:
        return s
"""

src2 = """
def test():
    s = 0
    for i in range(3):
        try:
            s += 10 // (i + 1)
        except ZeroDivisionError:
            s -= 1
    return s
"""

from dis import get_instructions
def norm(code_obj):
    return tuple(i.opname for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

c1 = compile(src1, '<s1>', 'exec')
c2 = compile(src2, '<s2>', 'exec')
n1 = norm(c1.co_consts[0])
n2 = norm(c2.co_consts[0])
print(f"else: return s: {n1}")
print(f"return s:       {n2}")
print(f"MATCH: {n1 == n2}")
