"""Trace AST generation for validate_data to understand missing return False and continue."""
import sys, dis, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
from core.cfg.region_ast_generator import RegionASTGenerator

# Load original bytecode
f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
dp = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == 'DataProcessor'][0]
vd = [c for c in dp.co_consts if hasattr(c, 'co_name') and c.co_name == 'validate_data'][0]

# Build CFG
builder = CFGBuilder()
cfg = builder.build(vd)

# Analyze regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Generate AST
gen = RegionASTGenerator(cfg, analyzer)
ast_dict = gen.generate()

def print_ast(node, indent=0):
    sp = "  " * indent
    if isinstance(node, list):
        for n in node:
            print_ast(n, indent)
        return
    if not isinstance(node, dict):
        print(f"{sp}{node}")
        return
    t = node.get('type', '?')
    print(f"{sp}{t}", end="")
    if 'test' in node:
        print(f" test={node['test']}", end="")
    if 'value' in node:
        print(f" value={node['value']}", end="")
    print()
    for k in ['body', 'orelse', 'finalbody', 'handlers']:
        if k in node and node[k]:
            print(f"{sp}  {k}:")
            print_ast(node[k], indent + 2)

print("=== validate_data AST ===")
print_ast(ast_dict)
