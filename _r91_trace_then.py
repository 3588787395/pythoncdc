#!/usr/bin/env python3
"""R91 trace then branch generation for outer IfRegion"""
import sys, marshal, types, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_price_common')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, analyzer)

# Find the outer IfRegion (entry=108)
outer_if = None
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 108:
        outer_if = r
        break

if outer_if:
    print("=== Outer IfRegion (entry=108) ===")
    print(f"  then_blocks: {[b.start_offset for b in outer_if.then_blocks]}")
    print(f"  else_blocks: {[b.start_offset for b in outer_if.else_blocks]}")
    
    # Check what blocks are already generated
    print(f"\n  Generated blocks before: {sorted([b.start_offset for b in ast_gen.generated_blocks])}")
    
    # Generate then branch
    try:
        then_stmts = ast_gen._if_generate_then_branch(outer_if)
        print(f"\n  Then branch stmts ({len(then_stmts)}):")
        for i, s in enumerate(then_stmts):
            print(f"    [{i}] type={s.get('type')}")
            if s.get('type') == 'Return':
                print(f"        value={s.get('value', {}).get('type') if s.get('value') else None}")
        
        print(f"\n  Generated blocks after then: {sorted([b.start_offset for b in ast_gen.generated_blocks])}")
    except Exception as e:
        import traceback
        print(f"  Error: {e}")
        traceback.print_exc()
