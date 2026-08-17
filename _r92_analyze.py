#!/usr/bin/env python3
"""R92 analyze get_history_common bytecode differences"""
import sys, marshal, types, dis
sys.path.insert(0, '.')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
decomp_src = decompile_pyc(target_pyc)

# Compile decompiled source
decomp_code = compile(decomp_src, '<decompiled>', 'exec')

# Find get_history_common in both
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

orig_func = find_function(orig_code, 'get_history_common')
decomp_func = find_function(decomp_code, 'get_history_common')

if orig_func and decomp_func:
    orig_instrs = list(dis.get_instructions(orig_func))
    decomp_instrs = list(dis.get_instructions(decomp_func))
    
    print(f"Original instructions: {len(orig_instrs)}")
    print(f"Decompiled instructions: {len(decomp_instrs)}")
    
    # Find first 10 true differences
    diffs = []
    min_len = min(len(orig_instrs), len(decomp_instrs))
    for i in range(min_len):
        oi = orig_instrs[i]
        di = decomp_instrs[i]
        if oi.opname != di.opname or oi.argval != di.argval:
            diffs.append((i, oi, di))
            if len(diffs) >= 20:
                break
    
    if len(orig_instrs) != len(decomp_instrs):
        print(f"Length mismatch: orig={len(orig_instrs)} decomp={len(decomp_instrs)}")
    
    print(f"\nFirst 20 differences:")
    for idx, oi, di in diffs:
        print(f"  idx={idx:4d} orig={oi.opname:30s} {str(oi.argval):30s} | decomp={di.opname:30s} {str(di.argval):30s}")
    
    # Also check the decompiled source
    lines = decomp_src.split('\n')
    in_func = False
    func_lines = []
    for i, line in enumerate(lines):
        if 'def get_history_common' in line:
            in_func = True
        if in_func:
            func_lines.append(line)
            if len(func_lines) > 50:
                break
    
    print(f"\nDecompiled source (first 50 lines):")
    for i, line in enumerate(func_lines):
        print(f"  {i+1:4d}: {line}")
