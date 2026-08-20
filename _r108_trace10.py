"""Check what generate() sees after analyze"""
import sys, marshal, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

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

# Call analyze first
gen.regions = gen.region_analyzer.analyze()

# Check the TryExceptRegion
for r in gen.regions:
    if hasattr(r, 'has_finally'):
        print(f"TryExceptRegion entry={r.entry.start_offset}")
        print(f"  has_else={r.has_else}")
        print(f"  else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else None}")
        print(f"  has_finally={r.has_finally}")
        print(f"  finally_copy_blocks={r.finally_copy_blocks}")
        # Now call _generate_try
        result = gen._generate_try(r)
        print(f"  result has orelse: {'orelse' in result}")
        if 'orelse' in result:
            print(f"  orelse: {json.dumps(result['orelse'], default=str)}")
