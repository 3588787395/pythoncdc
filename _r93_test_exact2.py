#!/usr/bin/env python3
"""R93 test: exact pattern of get_multiminute_his_data
if count_min == 0: with nested if-return, else with code, then return at top level"""
import sys, dis, types

# This matches the decompiled source exactly:
# Line 494: if count_min == 0:  (indent 8)
# Line 495:     his_data_dict = call()  (indent 12)
# Line 496:     if len(his_data_dict) == 0:  (indent 12)
# Line 497:         return his_data_dict  (indent 16)
# Line 498: else:  (indent 8)
# Line 499+:     ... lots of code ...  (indent 12)
# Line 549:     return his_data_dict  (indent 16, inside else)

# After the if-else, there should be code at indent 4 (top level of function)
# But the decompiled source has the return inside the else (indent 16)

# Let me test the exact source structure
src = '''
def test(a, b):
    if a:
        x = 1
        if b:
            return x
    else:
        y = 2
        z = get_call()
        return z
    return get_call()
'''

code = compile(src, '<test>', 'exec')
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test':
        print("=== Source with return at top level ===")
        for instr in dis.get_instructions(const):
            print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
        break

# Now test without the top-level return (return is inside else)
src2 = '''
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

code2 = compile(src2, '<test2>', 'exec')
for const in code2.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test':
        print("\n=== Source without top-level return ===")
        for instr in dis.get_instructions(const):
            print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
        break
