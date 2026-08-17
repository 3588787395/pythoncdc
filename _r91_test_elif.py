#!/usr/bin/env python3
"""R91 test: what generates LOAD_CONST None + RETURN_VALUE at elif chain end"""
import sys, dis, types

# Pattern A: elif chain all return, no else, no code after
srcA = '''
def test(a, b):
    if a:
        return None
    elif b:
        return None
'''

# Pattern B: elif chain all return, no else, code after (fallthrough)
srcB = '''
def test(a, b):
    if a:
        return None
    elif b:
        return None
    x = 1
    return x
'''

# Pattern C: if-else with all returns in both branches, code after
srcC = '''
def test(a, b):
    if a:
        return None
    else:
        if b:
            return None
        x = 1
    return x
'''

for name, src in [('A', srcA), ('B', srcB), ('C', srcC)]:
    code = compile(src, f'<test{name}>', 'exec')
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test':
            print(f"=== Pattern {name} ===")
            for instr in dis.get_instructions(const):
                if instr.offset < 50:
                    print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
            print()
            break
