"""Check CFGASTConverter and CFGCodeGenerator"""
import sys, marshal, json, ast
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

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

# Convert to Python AST
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)

# Check the function body
for node in py_ast.body:
    if isinstance(node, ast.FunctionDef):
        print(f"Function: {node.name}")
        for i, stmt in enumerate(node.body):
            print(f"  body[{i}]: {type(stmt).__name__}")
            if isinstance(stmt, ast.Return):
                print(f"    Return value: {ast.dump(stmt.value) if stmt.value else 'None'}")

# Generate source
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
print(f"\n=== Generated source ===")
print(source)
