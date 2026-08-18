#!/usr/bin/env python3
"""查看repro_05的异常表"""
import marshal
import types
import sys
import os

pyc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
    '.trae', 'specs', 'decompiler-test-comprehensive-10rounds', 'rounds', 'round_01', 'test_engineer', 'minimal_repros', 'repro_05_try_else_finally_return.pyc')

with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'integration_test':
        print(f"Function: {const.co_name}")
        print(f"co_exceptiontable: {const.co_exceptiontable.hex()}")
        print(f"co_consts: {const.co_consts}")
        print(f"co_varnames: {const.co_varnames}")
        
        # Parse exception table
        import dis
        print("\nException table entries:")
        try:
            for entry in dis.parse_exception_table(const):
                print(f"  start={entry.start} end={entry.end} target={entry.target} depth={entry.depth} lasti={entry.lasti}")
        except Exception as e:
            print(f"  Error parsing: {e}")
        
        print("\nInstructions:")
        for instr in dis.get_instructions(const):
            print(f"  {instr.offset:4d} {instr.opname:30s} {instr.arg if instr.arg is not None else '':>4} {instr.argval if instr.argval is not None else ''}")
        break
