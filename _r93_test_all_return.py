#!/usr/bin/env python3
"""R93 test: what generates LOAD_CONST None + RETURN_VALUE at merge point"""
import sys, dis, types

# Pattern A: if-then with nested if-else (all paths return in nested)
# followed by code at top level
srcA = '''
def test(a):
    if a:
        x = 1
        if x == 0:
            return x
        else:
            return x
    z = get_call()
    return z
'''

# Pattern B: same but nested if-else doesn't cover all paths
srcB = '''
def test(a):
    if a:
        x = 1
        if x == 0:
            return x
        else:
            y = 2
    z = get_call()
    return z
'''

# Pattern C: if-then where then body ends with if-elif (all return)
srcC = '''
def test(a):
    if a:
        x = 1
        if x == 0:
            return x
        elif x == 1:
            return x
    z = get_call()
    return z
'''

for name, src in [('A (nested if-else all return)', srcA), ('B (nested if-else not all return)', srcB), ('C (nested if-elif all return)', srcC)]:
    code = compile(src, f'<test>', 'exec')
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test':
            print(f"=== Pattern {name} ===")
            for instr in dis.get_instructions(const):
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
            print()
            break
