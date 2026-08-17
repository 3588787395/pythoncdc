#!/usr/bin/env python3
"""R92 analyze get_multiminute_his_data bytecode differences"""
import sys, marshal, types, dis
sys.path.insert(0, '.')
from pycdc import decompile_pyc

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
decomp_src = decompile_pyc(target_pyc)
decomp_code = compile(decomp_src, '<decompiled>', 'exec')

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

orig_func = find_function(orig_code, 'get_multiminute_his_data')
decomp_func = find_function(decomp_code, 'get_multiminute_his_data')

if orig_func and decomp_func:
    orig_instrs = list(dis.get_instructions(orig_func))
    decomp_instrs = list(dis.get_instructions(decomp_func))
    
    print(f"Original instructions: {len(orig_instrs)}")
    print(f"Decompiled instructions: {len(decomp_instrs)}")
    
    diffs = []
    min_len = min(len(orig_instrs), len(decomp_instrs))
    for i in range(min_len):
        oi = orig_instrs[i]
        di = decomp_instrs[i]
        if oi.opname != di.opname or oi.argval != di.argval:
            diffs.append((i, oi, di))
            if len(diffs) >= 15:
                break
    
    print(f"\nFirst 15 differences:")
    for idx, oi, di in diffs:
        print(f"  idx={idx:4d} orig={oi.opname:30s} {str(oi.argval):30s} | decomp={di.opname:30s} {str(di.argval):30s}")
    
    # Show decompiled source
    lines = decomp_src.split('\n')
    in_func = False
    func_lines = []
    for i, line in enumerate(lines):
        if 'def get_multiminute_his_data' in line:
            in_func = True
        if in_func:
            func_lines.append(line)
            if len(func_lines) > 40:
                break
    
    print(f"\nDecompiled source (first 40 lines):")
    for i, line in enumerate(func_lines):
        print(f"  {i+1:4d}: {line}")
