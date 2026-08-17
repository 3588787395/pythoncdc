#!/usr/bin/env python3
"""Round 02: Fixed verification handling duplicate code object names"""
import sys
import types
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

# Collect codes as ordered list (not dict) to handle duplicates
def _collect_codes_ordered(code, prefix=''):
    codes = [(prefix + code.co_name, code)]
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            child_prefix = prefix + code.co_name + '.'
            codes.extend(_collect_codes_ordered(const, child_prefix))
    return codes

orig_list = _collect_codes_ordered(orig_code)
decomp_list = _collect_codes_ordered(decomp_code)

# Match by name + position (nth occurrence of each name)
from collections import defaultdict
orig_by_name = defaultdict(list)
decomp_by_name = defaultdict(list)
for name, code in orig_list:
    orig_by_name[name].append(code)
for name, code in decomp_list:
    decomp_by_name[name].append(code)

total = 0
matched = 0
mismatches = []

for name, orig_codes in orig_by_name.items():
    decomp_codes = decomp_by_name.get(name, [])
    for i, orig_func in enumerate(orig_codes):
        total += 1
        if i < len(decomp_codes):
            result = compare_bytecode(orig_func, decomp_codes[i])
            if result['match']:
                matched += 1
            else:
                mismatches.append({
                    'name': f"{name}[{i}]",
                    'true_diffs': len(result['true_diffs']),
                    'jump_diffs': len(result['jump_diffs']),
                    'first_diff': result['true_diffs'][0] if result['true_diffs'] else (result['jump_diffs'][0] if result['jump_diffs'] else None),
                })
        else:
            mismatches.append({
                'name': f"{name}[{i}]",
                'true_diffs': -1,
                'jump_diffs': -1,
                'first_diff': {'type': 'missing_function'},
            })

rate = matched / total * 100 if total > 0 else 0
print(f"Total: {total}, Matched: {matched}, Mismatches: {len(mismatches)}, Rate: {rate:.2f}%")
for m in mismatches:
    print(f"  {m['name']}: {m['true_diffs']}td/{m['jump_diffs']}jd")
    if m.get('first_diff'):
        print(f"    first_diff: {m['first_diff']}")
