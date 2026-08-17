#!/usr/bin/env python3
"""R94 测试工程师: 分析 klinedata.pyc 的不一致函数模式"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')

from base import compare_bytecode
import marshal, types
from collections import Counter

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"
ok_path = "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedataOK.py"

# Load original pyc
with open(pyc_path, 'rb') as f:
    magic = f.read(4)
    flags = int.from_bytes(f.read(4), 'little')
    if flags & 1:  # PEP 552
        f.read(8)
    else:
        f.read(8)  # timestamp + size
    orig_code = marshal.load(f)

# Load decompiled OK.py
with open(ok_path, 'r', encoding='utf-8') as f:
    source = f.read()
decomp_code = compile(source, ok_path, 'exec')

def extract_code_objects(code):
    result = {code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

orig_map = extract_code_objects(orig_code)
decomp_map = extract_code_objects(decomp_code)

total = len(orig_map)
matched = 0
mismatches = []

for name, orig_co in orig_map.items():
    if name not in decomp_map:
        continue
    decomp_co = decomp_map[name]
    result = compare_bytecode(orig_co, decomp_co)
    if result.get('match', False):
        matched += 1
    else:
        true_diffs = result.get('true_diffs', [])
        jump_diffs = result.get('jump_diffs', [])
        fd = true_diffs[0] if true_diffs else (jump_diffs[0] if jump_diffs else {})
        mismatches.append({
            'name': name,
            'orig_count': result.get('orig_count', 0),
            'decomp_count': result.get('decomp_count', 0),
            'jump_diffs': len(jump_diffs),
            'true_diffs': len(true_diffs),
            'first_diff': fd,
        })

print(f"Total functions: {total}")
print(f"Matched: {matched}")
print(f"Match rate: {matched/total:.4f}")
print(f"Mismatches: {len(mismatches)}")
print()

# Categorize by first_diff pattern
pattern_counter = Counter()
for m in mismatches:
    fd = m['first_diff']
    orig_op = fd.get('orig_op', '?')
    decomp_op = fd.get('decomp_op', '?')
    orig_arg = fd.get('orig_arg', '?')
    decomp_arg = fd.get('decomp_arg', '?')
    # Simplify arg
    if isinstance(orig_arg, str) and len(orig_arg) > 30:
        orig_arg = orig_arg[:30] + '...'
    if isinstance(decomp_arg, str) and len(decomp_arg) > 30:
        decomp_arg = decomp_arg[:30] + '...'
    pattern = f"{orig_op}({orig_arg}) -> {decomp_op}({decomp_arg})"
    pattern_counter[pattern] += 1

# Sort by true_diffs descending
mismatches.sort(key=lambda x: x['true_diffs'], reverse=True)

for m in mismatches:
    fd = m['first_diff']
    orig_arg = fd.get('orig_arg', '?')
    decomp_arg = fd.get('decomp_arg', '?')
    if isinstance(orig_arg, str) and len(orig_arg) > 40:
        orig_arg = orig_arg[:40] + '...'
    if isinstance(decomp_arg, str) and len(decomp_arg) > 40:
        decomp_arg = decomp_arg[:40] + '...'
    print(f"  {m['name']}: orig={m['orig_count']} decomp={m['decomp_count']} jump={m['jump_diffs']} true={m['true_diffs']}")
    print(f"    first_diff: idx={fd.get('index','?')} {fd.get('orig_op','?')}({orig_arg}) -> {fd.get('decomp_op','?')}({decomp_arg})")
    print()

print("\nPattern summary:")
for pat, count in pattern_counter.most_common():
    print(f"  {count}x  {pat}")
