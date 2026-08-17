#!/usr/bin/env python3
"""R94: Trace ALL _generate_try calls"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator
import core.cfg.region_ast_generator as rag

_orig_generate_try = RegionASTGenerator._generate_try
_call_count = [0]

def _traced_generate_try(self, region, *args, **kwargs):
    _call_count[0] += 1
    count = _call_count[0]
    
    # Check if this region's handler blocks contain system_log + FORMAT_VALUE (f-string)
    has_system_log = False
    has_format_value = False
    has_error_info = False
    has_get_traceback = False
    
    for handler in region.handler_blocks:
        for instr in handler.instructions:
            if instr.opname == 'LOAD_GLOBAL' and instr.argval == 'get_traceback_message':
                has_get_traceback = True
            if instr.opname == 'LOAD_GLOBAL' and instr.argval == 'system_log':
                has_system_log = True
            if instr.opname == 'FORMAT_VALUE':
                has_format_value = True
            if instr.opname == 'STORE_FAST' and instr.argval == 'error_info':
                has_error_info = True
    
    if has_get_traceback and has_error_info:
        print(f"\n[GENERATE_TRY #{count}] TARGET: try region with get_traceback + error_info")
        print(f"  Region type: {region.region_type}")
        print(f"  try_blocks: {len(region.try_blocks)}")
        for tb in region.try_blocks:
            print(f"    try_block start={tb.start_offset} end={tb.end_offset}")
        print(f"  handler_blocks: {len(region.handler_blocks)}")
        for hb in region.handler_blocks:
            print(f"    handler_block start={hb.start_offset} end={hb.end_offset} instr_count={len(hb.instructions)}")
            # Show first 5 and last 5 instructions
            for i, instr in enumerate(hb.instructions[:5]):
                argval = instr.argval
                if isinstance(argval, str) and len(argval) > 30:
                    argval = argval[:30] + '...'
                print(f"      [{i}] offset={instr.offset} {instr.opname}({argval})")
            if len(hb.instructions) > 10:
                print(f"      ... ({len(hb.instructions) - 10} more)")
            for i, instr in enumerate(hb.instructions[-5:]):
                argval = instr.argval
                if isinstance(argval, str) and len(argval) > 30:
                    argval = argval[:30] + '...'
                print(f"      [{len(hb.instructions)-5+i}] offset={instr.offset} {instr.opname}({argval})")
        
        result = _orig_generate_try(self, region, *args, **kwargs)
        
        print(f"\n  Result type: {type(result).__name__}")
        if isinstance(result, dict):
            print(f"    dict type: {result.get('type')}")
            if 'handlers' in result:
                for h in result['handlers']:
                    print(f"    handler: type={h.get('type')} body_len={len(h.get('body', []))}")
        
        return result
    
    return _orig_generate_try(self, region, *args, **kwargs)

RegionASTGenerator._generate_try = _traced_generate_try

from pycdc import decompile_pyc
PYC = "f:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"
src = decompile_pyc(PYC)

print(f"\n[TRACE] _generate_try called {_call_count[0]} times total")

# Check the output for get_kline_by_date_one
if 'def get_kline_by_date_one' in src:
    idx = src.index('def get_kline_by_date_one')
    end_idx = src.find('\ndef ', idx + 10)
    if end_idx == -1:
        end_idx = idx + 800
    print(f"\n=== get_kline_by_date_one source ===")
    print(src[idx:end_idx])
