#!/usr/bin/env python3
"""R93 test: what generates LOAD_CONST None + RETURN_VALUE instead of JUMP_FORWARD"""
import sys, dis, types

# Pattern: if-then with nested if-elif (all return in then path),
# else has code, then code continues after if-else
# This is the exact pattern of get_multiminute_his_data
src_correct = '''
def test(a, b):
    if a:
        x = 1
        if b:
            return x
        else:
            y = 2
    else:
        z = get_call()
    return z
'''

# What if the else is missing (decompiler drops it)?
src_no_else = '''
def test(a, b):
    if a:
        x = 1
        if b:
            return x
        else:
            y = 2
    return get_call()
'''

# What if the else code is inside the then body?
src_else_inside = '''
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

for name, src in [('Correct', src_correct), ('No else', src_no_else), ('Else inside then', src_else_inside)]:
    code = compile(src, f'<test>', 'exec')
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test':
            print(f"=== {name} ===")
            for instr in dis.get_instructions(const):
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
            print()
            break
