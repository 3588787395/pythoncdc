#!/usr/bin/env python3
"""R94: Trace which method processes get_kline_by_date_one except handler"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator
import core.cfg.region_ast_generator as rag

# Patch both _generate_handler_body_statements and _generate_block_statements
_orig_handler = RegionASTGenerator._generate_handler_body_statements
_orig_block = RegionASTGenerator._generate_block_statements

def _traced_handler(self, block):
    has_traceback = any(i.opname == 'LOAD_GLOBAL' and i.argval == 'get_traceback_message' for i in block.instructions)
    has_system_log = any(i.opname == 'LOAD_GLOBAL' and i.argval == 'system_log' for i in block.instructions)
    has_format_value = any(i.opname == 'FORMAT_VALUE' for i in block.instructions)
    has_error_info = any(i.opname == 'STORE_FAST' and i.argval == 'error_info' for i in block.instructions)
    
    # get_kline_by_date_one handler: offset 800, has FORMAT_VALUE + error_info but NOT using .format()
    # It uses f-string (FORMAT_VALUE + BUILD_STRING)
    if has_traceback and has_error_info and has_format_value and not any(i.opname == 'LOAD_METHOD' and i.argval == 'format' for i in block.instructions):
        print(f"\n[HANDLER TRACE] TARGET: get_kline_by_date_one-like block")
        print(f"  Block start_offset={block.start_offset}, end={block.end_offset}")
        print(f"  Block role: {self.region_analyzer.get_block_role(block) if hasattr(self, 'region_analyzer') else 'N/A'}")
        print(f"  Block instructions ({len(block.instructions)}):")
        for i, instr in enumerate(block.instructions):
            argval = instr.argval
            if isinstance(argval, str) and len(argval) > 40:
                argval = argval[:40] + '...'
            print(f"    [{i}] offset={instr.offset} {instr.opname}({argval})")
        
        result = _orig_handler(self, block)
        
        print(f"\n  HANDLER Result ({len(result)} statements):")
        for i, stmt in enumerate(result):
            print(f"    [{i}] type={stmt.get('type')}")
        
        return result
    
    return _orig_handler(self, block)

def _traced_block(self, block, *args, **kwargs):
    has_traceback = any(i.opname == 'LOAD_GLOBAL' and i.argval == 'get_traceback_message' for i in block.instructions)
    has_format_value = any(i.opname == 'FORMAT_VALUE' for i in block.instructions)
    has_error_info = any(i.opname == 'STORE_FAST' and i.argval == 'error_info' for i in block.instructions)
    
    if has_traceback and has_error_info and has_format_value and not any(i.opname == 'LOAD_METHOD' and i.argval == 'format' for i in block.instructions):
        print(f"\n[BLOCK TRACE] TARGET: get_kline_by_date_one-like block")
        print(f"  Block start_offset={block.start_offset}, end={block.end_offset}")
        print(f"  Block role: {self.region_analyzer.get_block_role(block) if hasattr(self, 'region_analyzer') else 'N/A'}")
        print(f"  Block instructions ({len(block.instructions)}):")
        for i, instr in enumerate(block.instructions):
            argval = instr.argval
            if isinstance(argval, str) and len(argval) > 40:
                argval = argval[:40] + '...'
            print(f"    [{i}] offset={instr.offset} {instr.opname}({argval})")
        
        result = _orig_block(self, block, *args, **kwargs)
        
        print(f"\n  BLOCK Result ({len(result)} statements):")
        for i, stmt in enumerate(result):
            print(f"    [{i}] type={stmt.get('type')}")
        
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
    print(f"\n=== get_kline_by_date_one source ===")
    end_idx = src.find('\ndef ', idx + 10)
    if end_idx == -1:
        end_idx = idx + 600
    print(src[idx:end_idx])
