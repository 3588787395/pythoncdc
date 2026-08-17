#!/usr/bin/env python3
"""R91 trace nested IfRegion else branch generation"""
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

# Find the nested IfRegion at entry=280
nested_if = None
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 280:
        nested_if = r
        break

if nested_if:
    print(f"=== Nested IfRegion (entry=280) ===")
    print(f"  region_type: {nested_if.region_type}")
    print(f"  condition_block: {nested_if.condition_block.start_offset if nested_if.condition_block else '?'}")
    print(f"  then_blocks: {[b.start_offset for b in nested_if.then_blocks]}")
    print(f"  else_blocks: {[b.start_offset for b in nested_if.else_blocks]}")
    print(f"  parent: {type(nested_if.parent).__name__ if nested_if.parent else None}")
    
    # Check if there are elif conditions
    if hasattr(nested_if, 'elif_conditions'):
        print(f"  elif_conditions: {[b.start_offset for b in nested_if.elif_conditions] if nested_if.elif_conditions else []}")
    if hasattr(nested_if, 'elif_bodies'):
        print(f"  elif_bodies: {[[b.start_offset for b in bodies] for bodies in nested_if.elif_bodies] if nested_if.elif_bodies else []}")
    
    # Generate the nested IfRegion
    print(f"\n  Generated blocks before: {sorted([b.start_offset for b in ast_gen.generated_blocks])}")
    try:
        result = ast_gen._generate_if(nested_if)
        if isinstance(result, dict):
            print(f"\n  Result type={result.get('type')}")
            if result.get('type') == 'If':
                body = result.get('body', [])
                orelse = result.get('orelse', [])
                print(f"  body ({len(body)} stmts): {[s.get('type') for s in body]}")
                print(f"  orelse ({len(orelse)} stmts): {[s.get('type') for s in orelse]}")
        elif isinstance(result, list):
            print(f"\n  Result: {len(result)} items")
            for i, item in enumerate(result):
                print(f"    [{i}] type={item.get('type') if isinstance(item, dict) else type(item).__name__}")
    except Exception as e:
        import traceback
        print(f"  Error: {e}")
        traceback.print_exc()
    
    print(f"\n  Generated blocks after: {sorted([b.start_offset for b in ast_gen.generated_blocks])}")
else:
    print("Nested IfRegion at entry=280 not found!")
