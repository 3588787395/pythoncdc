#!/usr/bin/env python3
"""R94: Full trace of get_kline_by_date_one - trace all region/AST methods"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator
import core.cfg.region_ast_generator as rag

# Patch _generate_try to trace
_orig_generate_try = RegionASTGenerator._generate_try if hasattr(RegionASTGenerator, '_generate_try') else None

# Patch _generate_handler_body_statements
_orig_handler = RegionASTGenerator._generate_handler_body_statements
_orig_block = RegionASTGenerator._generate_block_statements

# Track all blocks processed
_all_blocks_processed = []

def _traced_handler(self, block):
    _all_blocks_processed.append(('handler', block.start_offset, len(block.instructions)))
    has_system_log = any(i.opname == 'LOAD_GLOBAL' and i.argval == 'system_log' for i in block.instructions)
    has_error_info = any(i.opname == 'STORE_FAST' and i.argval == 'error_info' for i in block.instructions)
    has_fields = any(i.opname == 'LOAD_FAST' and i.argval == 'fields' for i in block.instructions)
    
    if has_system_log or (has_error_info and has_fields):
        print(f"\n[HANDLER] block@{block.start_offset} ({len(block.instructions)} instrs)")
        for i, instr in enumerate(block.instructions):
            argval = instr.argval
            if isinstance(argval, str) and len(argval) > 40:
                argval = argval[:40] + '...'
            print(f"  [{i}] off={instr.offset} {instr.opname}({argval})")
        
        result = _orig_handler(self, block)
        
        print(f"  -> {len(result)} statements: {[s.get('type') for s in result]}")
        return result
    
    return _orig_handler(self, block)

def _traced_block(self, block, *args, **kwargs):
    _all_blocks_processed.append(('block', block.start_offset, len(block.instructions)))
    has_system_log = any(i.opname == 'LOAD_GLOBAL' and i.argval == 'system_log' for i in block.instructions)
    has_error_info = any(i.opname == 'STORE_FAST' and i.argval == 'error_info' for i in block.instructions)
    has_fields = any(i.opname == 'LOAD_FAST' and i.argval == 'fields' for i in block.instructions)
    has_push_exc = any(i.opname == 'PUSH_EXC_INFO' for i in block.instructions)
    
    if has_system_log or (has_error_info and has_fields) or has_push_exc:
        print(f"\n[BLOCK] block@{block.start_offset} ({len(block.instructions)} instrs)")
        for i, instr in enumerate(block.instructions):
            argval = instr.argval
            if isinstance(argval, str) and len(argval) > 40:
                argval = argval[:40] + '...'
            print(f"  [{i}] off={instr.offset} {instr.opname}({argval})")
        
        result = _orig_block(self, block, *args, **kwargs)
        
        print(f"  -> {len(result)} statements: {[s.get('type') for s in result]}")
        return result
    
    return _orig_block(self, block, *args, **kwargs)

RegionASTGenerator._generate_handler_body_statements = _traced_handler
RegionASTGenerator._generate_block_statements = _traced_block

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

print(f"\n=== All blocks processed ===")
for btype, boff, binstrs in _all_blocks_processed:
    print(f"  {btype}: block@{boff} ({binstrs} instrs)")
