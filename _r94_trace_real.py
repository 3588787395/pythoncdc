#!/usr/bin/env python3
"""R94: Monkey-patch _generate_handler_body_statements to trace execution"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator
import core.cfg.region_ast_generator as rag

_orig_method = RegionASTGenerator._generate_handler_body_statements

def _traced_method(self, block):
    # Check if this is the klinedata get_kline_by_date_one handler block
    is_target = False
    for instr in block.instructions:
        if instr.opname == 'LOAD_GLOBAL' and instr.argval == 'system_log':
            is_target = True
            break
    
    if is_target:
        print(f"\n[TRACE] _generate_handler_body_statements called for block with system_log")
        print(f"  Block instructions ({len(block.instructions)}):")
        for i, instr in enumerate(block.instructions):
            argval = instr.argval
            if isinstance(argval, str) and len(argval) > 40:
                argval = argval[:40] + '...'
            print(f"    [{i}] offset={instr.offset} {instr.opname}({argval})")
        
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
                val = stmt.get('value', {})
                print(f"        value type={val.get('type')}")
        
        return result
    
    return _orig_method(self, block)

RegionASTGenerator._generate_handler_body_statements = _traced_method

# Now decompile
from pycdc import decompile_pyc
PYC = "f:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"
src = decompile_pyc(PYC)
print(f"\n[TRACE] decompiled, source length: {len(src)}")
