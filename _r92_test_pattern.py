#!/usr/bin/env python3
"""R92 test: if-then with nested if-else that returns in then branch"""
import sys, dis, types

# Pattern matching get_multiminute_his_data
src_original = '''
def test(a, b):
    if a:
        x = 1
        if b:
            return x
        else:
            y = 2
    z = get_call()
    return z
'''

# What decompiler might produce (if-then without else, merge_block in then_blocks)
src_decompiled = '''
def test(a, b):
    if a:
        x = 1
        if b:
            return x
        else:
            y = 2
        return None
    z = get_call()
    return z
'''

for name, src in [('Original', src_original), ('Decompiled', src_decompiled)]:
    code = compile(src, f'<test_{name}>', 'exec')
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test':
            print(f"=== {name} ===")
            for instr in dis.get_instructions(const):
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
            print()
            break
