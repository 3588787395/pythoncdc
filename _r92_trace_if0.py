#!/usr/bin/env python3
"""R92 trace get_multiminute_his_data IfRegion@0 structure"""
import sys, marshal, types, dis
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

func_code = find_function(orig_code, 'get_multiminute_his_data')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, analyzer)

# Find IfRegion@0
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
        print(f"IfRegion@0 type={r.region_type.name} merge={r.merge_block.start_offset if r.merge_block else '?'}")
        print(f"  then_blocks: {[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
        print(f"  blocks: {[b.start_offset for b in r.blocks]}")
        
        # Check which then_blocks are >= merge_block
        if r.merge_block:
            mb = r.merge_block.start_offset
            post_mb = [b for b in r.then_blocks if b.start_offset >= mb]
            pre_mb = [b for b in r.then_blocks if b.start_offset < mb]
            print(f"  then_blocks before merge: {len(pre_mb)}")
            print(f"  then_blocks at/after merge: {len(post_mb)}")
            if post_mb:
                print(f"    post_merge_then: {[b.start_offset for b in post_mb]}")
        
        # Generate the IfRegion
        result = ast_gen._generate_if(r)
        if isinstance(result, dict) and result.get('type') == 'If':
            body = result.get('body', [])
            orelse = result.get('orelse', [])
            print(f"\n  Generated body: {len(body)} stmts")
            print(f"  Generated orelse: {len(orelse)} stmts")
            # Check last body statement
            if body:
                last = body[-1]
                print(f"  Last body stmt: type={last.get('type')}")
                if last.get('type') == 'Return':
                    val = last.get('value', {})
                    print(f"    return value={val.get('type') if val else None}")
        
        # Check generated blocks
        print(f"\n  Generated blocks after: {sorted([b.start_offset for b in ast_gen.generated_blocks])}")
        break
