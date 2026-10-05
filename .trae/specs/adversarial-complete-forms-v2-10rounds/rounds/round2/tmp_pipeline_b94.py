"""Temporary diagnostic: run full decompile pipeline on a single function code object."""
import sys, marshal

sys.path.insert(0, r"F:\Downloads\pythoncdc-main")

PYC = r"F:\Downloads\pythoncdc-main\test_repros\round2\x01_if_deep_hosts.pyc"
FUNC = sys.argv[1] if len(sys.argv) > 1 else 'if_in_while'

f = open(PYC, 'rb')
f.read(16)
module_code = marshal.load(f)

target = None
for const in module_code.co_consts:
    if hasattr(const, 'co_name') and const.co_name == FUNC:
        target = const
        break

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

cfg = build_cfg(target)
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
import json
print("=== AST DICT (truncated) ===")
def summ(d, depth=0):
    if isinstance(d, dict):
        keys = list(d.keys())
        print("  " * depth + "dict keys=" + str(keys[:12]))
        for k in keys:
            if k in ('body', 'orelse', 'finalbody', 'handlers', 'cases', 'items'):
                print("  " * depth + f" {k}:")
                for item in (d.get(k) or []):
                    summ(item, depth + 2)
            elif k in ('type', 'node_type', 'kind', 'test', 'value', 'name'):
                v = d[k]
                print("  " * depth + f" {k} = {v if not isinstance(v,(dict,)) else '<dict>'}")
    else:
        print("  " * depth + repr(d)[:100])
if isinstance(ast_dict, dict):
    summ(ast_dict)
else:
    print(type(ast_dict), repr(ast_dict)[:500])
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
print("=== SINGLE-FUNCTION PIPELINE OUTPUT ===")
print(source)
