#!/usr/bin/env python3
"""R92 test: Python compiler behavior for if-then ending with if-else"""
import sys, dis, types

# Pattern A: if-then with nested if-else, then branch returns in one path
srcA = '''
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

# Pattern B: Same but with explicit "pass" after if-else inside then
srcB = '''
def test(a, b):
    if a:
        x = 1
        if b:
            return x
        else:
            y = 2
        pass
    z = get_call()
    return z
'''

# Pattern C: with explicit "None" return
srcC = '''
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

for name, src in [('A (no extra)', srcA), ('B (with pass)', srcB), ('C (with return None)', srcC)]:
    code = compile(src, f'<test_{name}>', 'exec')
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test':
            print(f"=== Pattern {name} ===")
            for instr in dis.get_instructions(const):
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
            print()
            break
