#!/usr/bin/env python3
"""R93 test: what generates LOAD_CONST None + RETURN_VALUE at end of then branch"""
import sys, dis, types

# Original structure (what the source should look like)
src_original = '''
def test(a, b):
    if a:
        x = 1
        if b:
            return x
        else:
            y = 2
            for i in range(3):
                z = i
            return z
    return get_call()
'''

# Decompiled structure (everything inside the if, no code after)
src_decompiled = '''
def test(a, b):
    if a:
        x = 1
        if b:
            return x
        else:
            y = 2
            for i in range(3):
                z = i
            return z
        return None
    return get_call()
'''

for name, src in [('Original', src_original), ('Decompiled (with return None)', src_decompiled)]:
    code = compile(src, f'<test>', 'exec')
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test':
            print(f"=== {name} ===")
            for instr in dis.get_instructions(const):
                print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
            print()
            break
