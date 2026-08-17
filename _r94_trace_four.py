#!/usr/bin/env python3
"""R94: Trace _generate_try and except handler generation for get_kline_by_date_one"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator
import core.cfg.region_ast_generator as rag

_orig_generate_try = RegionASTGenerator._generate_try

def _traced_generate_try(self, region, *args, **kwargs):
    # Check if this try region contains the get_kline_by_date_one handler
    has_get_traceback = False
    has_system_log = False
    has_format_value = False
    has_error_info = False
    
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
    
    if has_get_traceback and has_error_info and has_format_value:
        print(f"\n[GENERATE_TRY TRACE] TARGET try region found!")
        print(f"  Region type: {region.region_type}")
        print(f"  try_blocks: {len(region.try_blocks)}")
        for tb in region.try_blocks:
            print(f"    try_block start={tb.start_offset} instructions={len(tb.instructions)}")
        print(f"  handler_blocks: {len(region.handler_blocks)}")
        for hb in region.handler_blocks:
            print(f"    handler_block start={hb.start_offset} instructions={len(hb.instructions)}")
            for i, instr in enumerate(hb.instructions):
                argval = instr.argval
                if isinstance(argval, str) and len(argval) > 40:
                    argval = argval[:40] + '...'
                print(f"      [{i}] offset={instr.offset} {instr.opname}({argval})")
        if region.merge_block:
            print(f"  merge_block start={region.merge_block.start_offset}")
        if region.else_blocks:
            print(f"  else_blocks: {len(region.else_blocks)}")
    
    return _orig_generate_try(self, region, *args, **kwargs)

RegionASTGenerator._generate_try = _traced_generate_try

# Now decompile
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
