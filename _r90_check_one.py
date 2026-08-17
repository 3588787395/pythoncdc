#!/usr/bin/env python3
import sys, marshal, types
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

target_pyc = 'site-packages/IQCommon/api/klinedata.pyc'
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

name = 'get_kline_by_count_new'
if name in orig_funcs and name in decomp_funcs:
    result = compare_bytecode(orig_funcs[name], decomp_funcs[name])
    print(f'{name}: match={result["match"]}, true_diffs={len(result["true_diffs"])}, jump_diffs={len(result["jump_diffs"])}')
    if result['true_diffs']:
        fd = result['true_diffs'][0]
        print(f'  first: idx={fd.get("index","?")} orig={fd.get("orig_op","?")}({fd.get("orig_arg","?")}) decomp={fd.get("decomp_op","?")}({fd.get("decomp_arg","?")})')
else:
    print(f'{name}: orig={name in orig_funcs}, decomp={name in decomp_funcs}')
