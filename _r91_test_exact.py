#!/usr/bin/env python3
"""R91 test exact patterns to find bytecode difference"""
import sys, dis, types

# Pattern matching the original source structure
src_original = '''
def test(frequency, start_date, count, trading_dates):
    if frequency:
        if start_date is not None:
            return None
        elif count is None:
            return None
        elif count <= 0:
            return None
    elif start_date is None:
        if count is None:
            return None
        elif count <= 0:
            return None
    else:
        if count is not None:
            return None
    if trading_dates is None:
        trading_dates = 1
    return trading_dates
'''

# Pattern matching what decompiler produces (elif instead of else)
src_decompiled = '''
def test(frequency, start_date, count, trading_dates):
    if frequency:
        if start_date is not None:
            return None
        elif count is None:
            return None
        elif count <= 0:
            return None
    elif start_date is None:
        if count is None:
            return None
        elif count <= 0:
            return None
    elif count is not None:
        return None
    if trading_dates is None:
        trading_dates = 1
    return trading_dates
'''

for name, src in [('Original', src_original), ('Decompiled', src_decompiled)]:
    code = compile(src, f'<test_{name}>', 'exec')
    for const in code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test':
            print(f"=== {name} ===")
            for instr in dis.get_instructions(const):
                if instr.offset < 100:
                    print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
            print()
            break
