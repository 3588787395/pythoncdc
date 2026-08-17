#!/usr/bin/env python3
"""R91 check original bytecode control flow around offset 278"""
import sys, dis, marshal, types

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_price_common')
print("Original bytecode around offset 260-450:")
for instr in dis.get_instructions(func_code):
    if 260 <= instr.offset <= 450:
        print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
