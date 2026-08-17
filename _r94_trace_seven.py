#!/usr/bin/env python3
"""R94: Trace _generate_try with correct attribute names"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator
import core.cfg.region_ast_generator as rag

_orig_generate_try = RegionASTGenerator._generate_try

def _traced_generate_try(self, region, *args, **kwargs):
    # Check except_handlers for system_log + error_info
    has_target = False
    for exc_type, exc_name, handler_blocks in region.except_handlers:
        for hb in handler_blocks:
            for instr in hb.instructions:
                if (instr.opname == 'LOAD_GLOBAL' and instr.argval == 'get_traceback_message'):
                    has_target = True
                    break
    
    if has_target:
        print(f"\n[GENERATE_TRY TRACE] TARGET: try region with get_traceback_message")
        print(f"  Region type: {region.region_type}")
        print(f"  try_blocks: {len(region.try_blocks)}")
        for tb in region.try_blocks[:3]:
            print(f"    try_block start={tb.start_offset} end={tb.end_offset}")
        print(f"  except_handlers: {len(region.except_handlers)}")
        for exc_type, exc_name, handler_blocks in region.except_handlers:
            print(f"    handler: exc_type={exc_type} exc_name={exc_name} blocks={len(handler_blocks)}")
            for hb in handler_blocks:
                print(f"      block start={hb.start_offset} end={hb.end_offset} instr_count={len(hb.instructions)}")
                for i, instr in enumerate(hb.instructions):
                    argval = instr.argval
                    if isinstance(argval, str) and len(argval) > 30:
                        argval = argval[:30] + '...'
                    print(f"        [{i}] offset={instr.offset} {instr.opname}({argval})")
        print(f"  handler_entry_blocks: {[b.start_offset for b in region.handler_entry_blocks]}")
        if region.else_blocks:
            print(f"  else_blocks: {len(region.else_blocks)}")
        if region.merge_block:
            print(f"  merge_block start={region.merge_block.start_offset}")
    
    result = _orig_generate_try(self, region, *args, **kwargs)
    
    if has_target:
        print(f"\n  Result type: {result.get('type') if isinstance(result, dict) else type(result).__name__}")
        if isinstance(result, dict) and 'handlers' in result:
            for h in result['handlers']:
                body = h.get('body', [])
                print(f"    handler: type={h.get('type')} body_len={len(body)} body_types={[s.get('type') for s in body if isinstance(s, dict)]}")
    
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
