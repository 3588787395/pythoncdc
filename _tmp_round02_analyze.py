#!/usr/bin/env python3
"""Round 02: Analyze mismatches in detail"""
import sys
import os
import dis
import types
import importlib.util
import marshal

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

spec = importlib.util.spec_from_file_location('test_mod', 'python_syntax_comprehensive_test.pyc')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with open('python_syntax_comprehensive_test.pyc', 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

import py_compile
py_compile.compile('python_syntax_comprehensive_testOK.py', 'python_syntax_comprehensive_testOK.pyc', doraise=True)
with open('python_syntax_comprehensive_testOK.pyc', 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

exec(open('testqouter/round1/base.py', encoding='utf-8').read())

def _collect_codes(code, prefix=''):
    codes = [(prefix + code.co_name, code)]
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = prefix + code.co_name + '.'
            codes.extend(_collect_codes(const, child_prefix))
    return codes

orig_codes = dict(_collect_codes(orig_code))
decomp_codes = dict(_collect_codes(decomp_code))

# Show all code names
print("Original code names:", [k for k in sorted(orig_codes.keys())])
print()

# Show detailed diffs for top mismatches
targets = ['<module>.exception_handling_examples', '<module>.control_flow_examples', 
           '<module>.<listcomp>', '<module>.<lambda>', '<module>.multiple_coroutines']
for name in targets:
    if name in orig_codes and name in decomp_codes:
        result = compare_bytecode(orig_codes[name], decomp_codes[name])
        print(f"\n{'='*60}")
        print(f"Function: {name}")
        print(f"  true_diffs: {len(result['true_diffs'])}, jump_diffs: {len(result['jump_diffs'])}")
        
        all_diffs = result['true_diffs'][:15]
        for i, d in enumerate(all_diffs):
            print(f"  td[{i}]: {d}")
        for i, d in enumerate(result['jump_diffs'][:5]):
            print(f"  jd[{i}]: {d}")
    elif name in orig_codes:
        print(f"\n{name}: MISSING in decompiled!")
