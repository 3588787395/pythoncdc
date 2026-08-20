"""Check CFGASTConverter detail"""
import sys, marshal, json, ast
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter

pyc_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_07_finally_implicit_return.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func_code = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_finally_implicit_return':
        func_code = c
        break

cfg = build_cfg(func_code)
gen = RegionASTGenerator(cfg)
ast_dict = gen.generate()

# Check the dict AST
print("=== Dict AST body types ===")
for i, node in enumerate(ast_dict.get('body', [])):
    if isinstance(node, dict):
        print(f"  body[{i}]: type={node.get('type')}")

# Convert to Python AST
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)

# Check the Python AST
print("\n=== Python AST ===")
print(ast.dump(py_ast, indent=2)[:3000])
