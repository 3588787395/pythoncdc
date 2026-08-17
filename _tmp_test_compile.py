#!/usr/bin/env python3
"""Test: does break in for-else compile correctly?"""
import sys
import dis
sys.stdout.reconfigure(encoding='utf-8')

# Test 1: break in for-else
src1 = """
for item in my_list:
    if item == 3:
        break
else:
    print('not found')
"""
code1 = compile(src1, '<test>', 'exec')
print("=== Test 1: break in for-else ===")
for i in dis.get_instructions(code1):
    print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")

# Test 2: break in for-else with return in else
src2 = """
for item in my_list:
    if item == 3:
        break
else:
    print('not found')
    return result
"""
code2 = compile(src2, '<test>', 'exec')
print("\n=== Test 2: break in for-else with return in else ===")
for i in dis.get_instructions(code2):
    print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
