#!/usr/bin/env python3
"""R94: Trace _generate_try for ALL try regions in get_kline_by_date_one"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator
import core.cfg.region_ast_generator as rag

_orig_generate_try = RegionASTGenerator._generate_try

def _traced_generate_try(self, region, *args, **kwargs):
    # Print ALL try regions
    print(f"\n[GENERATE_TRY] Region type={region.region_type}")
    print(f"  try_blocks: {len(region.try_blocks)}")
    for tb in region.try_blocks:
        print(f"    try_block start={tb.start_offset} end={tb.end_offset} instr_count={len(tb.instructions)}")
    print(f"  handler_blocks: {len(region.handler_blocks)}")
    for hb in region.handler_blocks:
        print(f"    handler_block start={hb.start_offset} end={hb.end_offset} instr_count={len(hb.instructions)}")
        # Show all instructions
        for i, instr in enumerate(hb.instructions):
            argval = instr.argval
            if isinstance(argval, str) and len(argval) > 30:
                argval = argval[:30] + '...'
            print(f"      [{i}] offset={instr.offset} {instr.opname}({argval})")
    if hasattr(region, 'merge_block') and region.merge_block:
        print(f"  merge_block start={region.merge_block.start_offset}")
    if hasattr(region, 'else_blocks') and region.else_blocks:
        print(f"  else_blocks: {len(region.else_blocks)}")
    
    result = _orig_generate_try(self, region, *args, **kwargs)
    
    if isinstance(result, dict):
        print(f"  Result type: {result.get('type')}")
        if 'handlers' in result:
            for h in result['handlers']:
                body = h.get('body', [])
                print(f"    handler body_len={len(body)} body_types={[s.get('type') for s in body if isinstance(s, dict)]}")
    
    return result

RegionASTGenerator._generate_try = _traced_generate_try

from pycdc import decompile_pyc
PYC = "f:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"
src = decompile_pyc(PYC)

# Check the output for get_kline_by_date_one
if 'def get_kline_by_date_one' in src:
    idx = src.index('def get_kline_by_date_one')
    end_idx = src.find('\ndef ', idx + 10)
    if end_idx == -1:
        end_idx = idx + 800
    print(f"\n=== get_kline_by_date_one source ===")
    print(src[idx:end_idx])
