"""Check CFGCodeGenerator with ASTFunctionDef"""
import sys, marshal
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

# Check the dict AST
print("=== Dict AST body ===")
for i, node in enumerate(ast_dict.get('body', [])):
    if isinstance(node, dict):
        t = node.get('type')
        print(f"  body[{i}]: type={t}")
        if t == 'Return':
            print(f"    value: {node.get('value')}")

# Convert
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
print(f"\nConverted type: {type(py_ast).__name__}")

# Check if it's a module-like object
if hasattr(py_ast, 'body'):
    print(f"py_ast.body length: {len(py_ast.body)}")
    for i, node in enumerate(py_ast.body):
        print(f"  body[{i}]: {type(node).__name__}")
        if hasattr(node, 'body'):
            print(f"    node.body length: {len(node.body)}")
            for j, stmt in enumerate(node.body):
                print(f"    body[{j}]: {type(stmt).__name__}")

# Generate source
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
print(f"\n=== Source ===\n{source}")
