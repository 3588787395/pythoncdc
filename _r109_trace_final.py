"""Check final_integration_test AST"""
import sys, marshal, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

pyc_path = 'decompiler_test_comprehensive.cpython-311.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find DataProcessor class
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'DataProcessor':
        # Find final_integration_test
        for cc in c.co_consts:
            if hasattr(cc, 'co_name') and cc.co_name == 'final_integration_test':
                func_code = cc
                break
        break

cfg = build_cfg(func_code)
gen = RegionASTGenerator(cfg)
ast_dict = gen.generate()

# Print AST body types
print("=== AST body types ===")
for i, node in enumerate(ast_dict.get('body', [])):
    if isinstance(node, dict):
        t = node.get('type')
        print(f"  body[{i}]: type={t}")
        if t == 'Try':
            # Check finalbody
            fb = node.get('finalbody', [])
            print(f"    finalbody: {len(fb)} nodes")
            handlers = node.get('handlers', [])
            print(f"    handlers: {len(handlers)}")
            orelse = node.get('orelse', [])
            print(f"    orelse: {len(orelse)} nodes")
            for j, oe in enumerate(orelse):
                if isinstance(oe, dict):
                    print(f"      orelse[{j}]: type={oe.get('type')}")
        if t == 'Return':
            print(f"    value: {node.get('value')}")

# Check _filter_trailing_return_none
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)

# Check function body
if hasattr(py_ast, 'body'):
    for i, node in enumerate(py_ast.body):
        if hasattr(node, 'body'):
            print(f"\nFunction body ({len(node.body)} nodes):")
            for j, stmt in enumerate(node.body):
                from core.ast_nodes import ASTReturn, ASTTry
                print(f"  body[{j}]: {type(stmt).__name__}")
                if isinstance(stmt, ASTReturn):
                    print(f"    value: {stmt.value}")
