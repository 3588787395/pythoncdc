#!/usr/bin/env python3
"""Test: break in for-else inside function with code after"""
import sys
import dis
sys.stdout.reconfigure(encoding='utf-8')

# This matches the original structure: for-else with break, code after else
src = """
def test():
    for item in my_list:
        if item == 3:
            break
    else:
        print('not found')
    counter = 0
    while counter < 5:
        print(counter)
        counter += 1
"""
code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test':
        print("=== test() with code after for-else ===")
        for i in dis.get_instructions(c):
            print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
