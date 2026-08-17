#!/usr/bin/env python3
"""R94: Trace get_kline_by_date_one specifically"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator
import core.cfg.region_ast_generator as rag

_orig_method = RegionASTGenerator._generate_handler_body_statements

def _traced_method(self, block):
    # Check if this block contains 'get_traceback_message' + 'system_log' + 'error_info'
    has_traceback = any(i.opname == 'LOAD_GLOBAL' and i.argval == 'get_traceback_message' for i in block.instructions)
    has_system_log = any(i.opname == 'LOAD_GLOBAL' and i.argval == 'system_log' for i in block.instructions)
    has_error_info = any(i.opname == 'STORE_FAST' and i.argval == 'error_info' for i in block.instructions)
    
    if has_traceback and has_system_log and has_error_info:
        print(f"\n[TRACE] TARGET BLOCK found!")
        print(f"  Block start_offset={block.start_offset}")
        print(f"  Block instructions ({len(block.instructions)}):")
        for i, instr in enumerate(block.instructions):
            argval = instr.argval
            if isinstance(argval, str) and len(argval) > 40:
                argval = argval[:40] + '...'
            print(f"    [{i}] offset={instr.offset} {instr.opname}({argval})")
        
        # Also check what generated_blocks contains
        print(f"  block in generated_blocks: {block in self.generated_blocks}")
        print(f"  block role: {self.region_analyzer.get_block_role(block) if hasattr(self, 'region_analyzer') else 'N/A'}")
        
        result = _orig_method(self, block)
        
        print(f"\n  Result ({len(result)} statements):")
        for i, stmt in enumerate(result):
            print(f"    [{i}] type={stmt.get('type')}")
            if stmt.get('type') == 'Expr':
                val = stmt.get('value', {})
                print(f"        value type={val.get('type')}")
            elif stmt.get('type') == 'Assign':
                targets = stmt.get('targets', [])
                for t in targets:
                    print(f"        target={t.get('id', t.get('type'))}")
        
        return result
    
    return _orig_method(self, block)

RegionASTGenerator._generate_handler_body_statements = _traced_method

# Now decompile
from pycdc import decompile_pyc
PYC = "f:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"
src = decompile_pyc(PYC)
print(f"\n[TRACE] decompiled, source length: {len(src)}")

# Check the output for get_kline_by_date_one
if 'def get_kline_by_date_one' in src:
    idx = src.index('def get_kline_by_date_one')
    print(f"\n=== get_kline_by_date_one source ===")
    print(src[idx:idx+500])
