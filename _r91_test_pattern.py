#!/usr/bin/env python3
"""R91 minimal reproduction: if-elif-elif with all returns vs if-else with nested if"""
import sys, dis, marshal, types

# Pattern 1: Original code likely uses if/elif/elif (all return)
src1 = '''
def test(a, b, c):
    if a:
        if b:
            return None
        elif c:
            return None
        elif b > 0:
            return None
    elif a is None:
        if b is None:
            return None
        elif c <= 0:
            return None
        # code continues here (offset 438 equivalent)
        x = 1
    return x
'''

# Pattern 2: What decompiler produces (elif chain with implicit return)
src2 = '''
def test(a, b, c):
    if a:
        if b:
            return None
        elif c:
            return None
        elif b > 0:
            return None
    elif a is None:
        if b is None:
            return None
        elif c <= 0:
            return None
        else:
            pass
        x = 1
    return x
'''

code1 = compile(src1, '<test1>', 'exec')
code2 = compile(src2, '<test2>', 'exec')

for const in code1.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test':
        print("=== Pattern 1 (original, no else after elif) ===")
        for instr in dis.get_instructions(const):
            if instr.offset < 120:
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
        break

print()

for const in code2.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test':
        print("=== Pattern 2 (with else: pass) ===")
        for instr in dis.get_instructions(const):
            if instr.offset < 120:
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
        break
