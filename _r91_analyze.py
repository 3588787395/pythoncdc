#!/usr/bin/env python3
"""R91 analyze get_price_common bytecode differences"""
import sys, marshal, types, dis
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode, _filter_noise_instrs

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

decomp_src = decompile_pyc(target_pyc)
decomp_code = compile(decomp_src, '<decompiled>', 'exec')

def extract_functions(code):
    funcs = {}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            funcs[const.co_name] = const
            for inner in const.co_consts:
                if isinstance(inner, types.CodeType):
                    funcs[inner.co_name] = inner
    return funcs

orig_funcs = extract_functions(orig_code)
decomp_funcs = extract_functions(decomp_code)

name = 'get_price_common'
if name in orig_funcs and name in decomp_funcs:
    result = compare_bytecode(orig_funcs[name], decomp_funcs[name])
    print(f"{name}: match={result['match']}, true_diffs={len(result['true_diffs'])}, jump_diffs={len(result['jump_diffs'])}")
    
    # Show first 5 true diffs
    print("\nFirst 5 true diffs:")
    for d in result['true_diffs'][:5]:
        print(f"  idx={d.get('index','?')} orig={d.get('orig_op','?')}({d.get('orig_arg','?')}) decomp={d.get('decomp_op','?')}({d.get('decomp_arg','?')})")
    
    # Show original and decompiled bytecode around first diff
    orig_instrs = _filter_noise_instrs(list(dis.get_instructions(orig_funcs[name])))
    decomp_instrs = _filter_noise_instrs(list(dis.get_instructions(decomp_funcs[name])))
    
    first_idx = result['true_diffs'][0]['index'] if result['true_diffs'] else 0
    start = max(0, first_idx - 10)
    end = min(len(orig_instrs), first_idx + 20)
    
    print(f"\nOriginal bytecode (around idx {first_idx}, showing {start}-{end}):")
    for i in range(start, end):
        marker = " >>>" if i == first_idx else "    "
        arg = orig_instrs[i].argrepr if hasattr(orig_instrs[i], 'argrepr') else ''
        print(f"{marker} {i:3d} {orig_instrs[i].offset:4d} {orig_instrs[i].opname:25s} {arg}")
    
    print(f"\nDecompiled bytecode (around idx {first_idx}, showing {start}-{end}):")
    for i in range(start, min(end, len(decomp_instrs))):
        marker = " >>>" if i == first_idx else "    "
        arg = decomp_instrs[i].argrepr if hasattr(decomp_instrs[i], 'argrepr') else ''
        print(f"{marker} {i:3d} {decomp_instrs[i].offset:4d} {decomp_instrs[i].opname:25s} {arg}")
else:
    print(f"{name}: orig={name in orig_funcs}, decomp={name in decomp_funcs}")
