#!/usr/bin/env python3
"""R90 重新反编译 klinedata.pyc 并比较字节码"""
import sys, os, marshal, types, dis
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from pycdc import decompile_pyc as _pycdc_decompile
from testqouter.round1.base import compare_bytecode, _filter_noise_instrs

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"

# Load original pyc
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

# Decompile
decomp_src = _pycdc_decompile(target_pyc)
if not decomp_src:
    print("Decompilation failed!")
    sys.exit(1)

# Compile decompiled source
decomp_code = compile(decomp_src, '<decompiled>', 'exec')

# Extract functions
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

# Compare
matched = 0
total = 0
mismatched = []

all_names = set(orig_funcs.keys()) | set(decomp_funcs.keys())
for name in sorted(all_names):
    if name in orig_funcs and name in decomp_funcs:
        total += 1
        result = compare_bytecode(orig_funcs[name], decomp_funcs[name])
        if result['match'] or (not result['true_diffs'] and result.get('jump_only')):
            matched += 1
        else:
            td = len(result['true_diffs'])
            jd = len(result['jump_diffs'])
            fd = result['true_diffs'][0] if result['true_diffs'] else (result['jump_diffs'][0] if result['jump_diffs'] else {})
            mismatched.append((name, td, jd, fd))
    elif name in orig_funcs:
        total += 1
        mismatched.append((name, -1, 0, {}))
    elif name in decomp_funcs:
        mismatched.append((name, -2, 0, {}))

print(f"Match: {matched}/{total} = {matched/total*100:.2f}%")
print(f"Mismatched: {len(mismatched)}")
print()

mismatched.sort(key=lambda x: -(x[1] if x[1] > 0 else 999))
print("Mismatched (top 10):")
for name, td, jd, fd in mismatched[:10]:
    if td == -1:
        print(f"  MISSING - {name}")
    elif td == -2:
        print(f"  EXTRA   - {name}")
    else:
        print(f"  {td:4d} true_diffs, {jd:3d} jump_diffs - {name}")
        if fd:
            print(f"         first: idx={fd.get('index','?')} orig={fd.get('orig_op','?')}({fd.get('orig_arg','?')}) decomp={fd.get('decomp_op','?')}({fd.get('decomp_arg','?')})")
