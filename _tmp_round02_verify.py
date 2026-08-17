#!/usr/bin/env python3
"""Round 02: Verify exact mismatch count"""
import sys
import os
import types
import importlib.util
import marshal
import py_compile

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

exec(open('testqouter/round1/base.py', encoding='utf-8').read())

with open('python_syntax_comprehensive_test.pyc', 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

py_compile.compile('python_syntax_comprehensive_testOK.py', 'python_syntax_comprehensive_testOK.pyc', doraise=True)
with open('python_syntax_comprehensive_testOK.pyc', 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

def _collect_codes(code, prefix=''):
    codes = [(prefix + code.co_name, code)]
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = prefix + code.co_name + '.'
            codes.extend(_collect_codes(const, child_prefix))
    return codes

orig_list = _collect_codes(orig_code)
decomp_dict = {name: code for name, code in _collect_codes(decomp_code)}

total = len(orig_list)
matched = 0
mismatches = []

for name, orig_func in orig_list:
    if name in decomp_dict:
        result = compare_bytecode(orig_func, decomp_dict[name])
        if result['match']:
            matched += 1
        else:
            mismatches.append({
                'name': name,
                'true_diffs': len(result['true_diffs']),
                'jump_diffs': len(result['jump_diffs']),
                'first_diff': result['true_diffs'][0] if result['true_diffs'] else (result['jump_diffs'][0] if result['jump_diffs'] else None),
            })
    else:
        mismatches.append({
            'name': name,
            'true_diffs': -1,
            'jump_diffs': -1,
            'first_diff': {'type': 'missing_function'},
        })

rate = matched / total * 100 if total > 0 else 0
print(f"Total: {total}, Matched: {matched}, Mismatches: {len(mismatches)}, Rate: {rate:.2f}%")
for m in mismatches:
    print(f"  {m['name']}: {m['true_diffs']}td/{m['jump_diffs']}jd")
