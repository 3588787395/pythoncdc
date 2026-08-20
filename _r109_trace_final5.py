"""Check trailing_returns for final_integration_test"""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

pyc_path = 'decompiler_test_comprehensive.cpython-311.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'DataProcessor':
        for cc in c.co_consts:
            if hasattr(cc, 'co_name') and cc.co_name == 'final_integration_test':
                func_code = cc
                break
        break

cfg = build_cfg(func_code)
gen = RegionASTGenerator(cfg)
ast_dict = gen.generate()

print(f"Trailing returns: {gen._trailing_returns}")
print(f"Total regions: {len(gen.regions)}")
print(f"AST body length: {len(ast_dict.get('body', []))}")
for i, node in enumerate(ast_dict.get('body', [])):
    if isinstance(node, dict):
        print(f"  body[{i}]: type={node.get('type')}")

# Check blocks with RETURN_VALUE
for off in [784, 796, 810, 816]:
    b = cfg.get_block_by_offset(off)
    if b:
        instrs = [(i.opname, i.argval) for i in b.instructions if i.opname not in ('RESUME','NOP','CACHE')]
        print(f"Block {off}: {instrs}")
        print(f"  succs: {[s.start_offset for s in b.successors]}")
