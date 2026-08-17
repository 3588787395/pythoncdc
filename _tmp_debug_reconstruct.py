#!/usr/bin/env python3
"""Debug expr_reconstructor.reconstruct for multiple_coroutines"""
import sys
import os
import types
import importlib.util

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

# Load pyc
spec = importlib.util.spec_from_file_location('test_mod', 'python_syntax_comprehensive_test.pyc')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

import marshal
with open('python_syntax_comprehensive_test.pyc', 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

for const in orig_code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'multiple_coroutines':
        builder = CFGBuilder()
        cfg = builder.build(const)
        
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        
        gen = RegionASTGenerator(cfg, analyzer)
        
        # Get Block 2
        entry = cfg.entry_block
        print(f"entry_block offset={entry.start_offset}")
        print(f"  instructions:")
        for i in entry.instructions:
            print(f"    {i.offset:4d}: {i.opname:30s} {i.argval}")
        
        # Simulate _reconstruct_await_block_stmts
        _aw_stmt_instrs = []
        _aw_after_awaitable = False
        for _instr in entry.instructions:
            if _instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP'):
                continue
            if _instr.opname == 'GET_AWAITABLE':
                _aw_stmt_instrs.append(_instr)
                _aw_after_awaitable = True
                continue
            if _aw_after_awaitable and _instr.opname == 'LOAD_CONST' and _instr.argval is None:
                continue
            if _aw_after_awaitable and _instr.opname == 'SEND':
                continue
            if _instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD_NO_INTERRUPT'):
                break
            _aw_stmt_instrs.append(_instr)
        
        print(f"\n_aw_stmt_instrs ({len(_aw_stmt_instrs)}):")
        for i in _aw_stmt_instrs:
            print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
        
        # Try to reconstruct
        _aw_expr = gen.expr_reconstructor.reconstruct(_aw_stmt_instrs)
        print(f"\nreconstruct result: {_aw_expr}")
        if _aw_expr:
            print(f"  type: {_aw_expr.get('type')}")
        else:
            print("  RESULT IS None — reconstruction failed!")
            
            # Try without GET_AWAITABLE
            instrs_without_ga = [i for i in _aw_stmt_instrs if i.opname != 'GET_AWAITABLE']
            print(f"\nTrying without GET_AWAITABLE ({len(instrs_without_ga)} instrs):")
            expr2 = gen.expr_reconstructor.reconstruct(instrs_without_ga)
            print(f"  result: {expr2}")
            if expr2:
                print(f"  type: {expr2.get('type')}")
        break
