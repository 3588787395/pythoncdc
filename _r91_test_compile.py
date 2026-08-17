#!/usr/bin/env python3
"""Test what Python compiler generates for if-elif with all branches returning"""
import dis

# Test 1: Original pattern (if-elif with all returns + elif)
src1 = """
def test(a, b, c, d):
    if a:
        if b:
            return None
        elif c:
            return None
        elif d:
            return None
    elif b:
        return 1
    return 0
"""

code1 = compile(src1, '<test>', 'exec')
for const in code1.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'test':
        print("=== Test 1: if-elif with all returns + elif ===")
        for instr in dis.get_instructions(const):
            if instr.offset < 100:
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
        break

# Test 2: Without the extra return at the end
src2 = """
def test(a, b, c, d):
    if a:
        if b:
            return None
        elif c:
            return None
        elif d:
            return None
    elif b:
        return 1
"""

code2 = compile(src2, '<test>', 'exec')
for const in code2.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'test':
        print("\n=== Test 2: without trailing return ===")
        for instr in dis.get_instructions(const):
            if instr.offset < 100:
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
        break
