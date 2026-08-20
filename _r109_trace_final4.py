"""Check all regions in final_integration_test"""
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

print(f"Total regions: {len(gen.regions)}")
for r in gen.regions:
    print(f"  {type(r).__name__}: entry={r.entry_block.start_offset}, parent={'None' if r.parent is None else type(r.parent).__name__}")
