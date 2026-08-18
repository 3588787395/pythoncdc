#!/usr/bin/env python3
"""查看repro_r2_09的字节码"""
import dis, marshal, types, sys, os
pyc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    '.trae', 'specs', 'decompiler-test-comprehensive-10rounds', 'rounds', 'round_02', 'test_engineer', 'minimal_repros', 'repro_r2_09_multi_elif_break.pyc')
with open(pyc_path, 'rb') as f:
    f.read(16); code = marshal.load(f)
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test_multi_elif_break':
        for instr in dis.get_instructions(const):
            print(f"  {instr.offset:4d} {instr.opname:30s} {instr.arg if instr.arg is not None else '':>4} {instr.argval if instr.argval is not None else ''}")
        break
