#!/usr/bin/env python3
"""R92 check original bytecode around offset 2710"""
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

func_code = find_function(orig_code, 'get_multiminute_his_data')
print("Original bytecode around offset 2700-2770:")
for instr in dis.get_instructions(func_code):
    if 2700 <= instr.offset <= 2770:
        print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argrepr}")
