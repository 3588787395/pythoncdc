import sys, types, marshal, io, dis, os
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode
from pycdc import decompile_pyc

# Focus on tradingday_calendar.pyc - list ALL mismatched functions
pyc_path = 'site-packages/fly/common/tradingday_calendar.pyc'

with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

source = decompile_pyc(pyc_path)
decomp_code = compile(source, '<decompiled>', 'exec')

def extract_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const, f"{prefix}.{const.co_name}" if prefix else const.co_name))
    return result

orig_map = extract_code_objects(orig_code)
decomp_map = extract_code_objects(decomp_code)

common = set(orig_map.keys()) & set(decomp_map.keys())
missing = set(orig_map.keys()) - set(decomp_map.keys())
extra = set(decomp_map.keys()) - set(orig_map.keys())

print(f"Common: {len(common)}, Missing: {len(missing)}, Extra: {len(extra)}")
if missing:
    print(f"Missing: {sorted(missing)[:10]}")
if extra:
    print(f"Extra: {sorted(extra)[:10]}")

print("\n=== All mismatched functions ===")
matched = 0
mismatches = []
for name in sorted(common):
    cmp = compare_bytecode(orig_map[name], decomp_map[name])
    if cmp.get('match') or cmp.get('jump_only'):
        matched += 1
    else:
        true_diffs = cmp.get('true_diffs', [])
        jump_diffs = cmp.get('jump_diffs', [])
        mismatches.append((name, len(true_diffs), len(jump_diffs)))

for name, td, jd in mismatches:
    print(f"  {name}: true_diffs={td}, jump_diffs={jd}")

print(f"\nMatched: {matched}/{len(common)}")

# Show <module> first diff details
if '<module>' in orig_map:
    name = '<module>'
    cmp = compare_bytecode(orig_map[name], decomp_map.get(name))
    if not cmp.get('match') and not cmp.get('jump_only'):
        true_diffs = cmp.get('true_diffs', [])
        print(f"\n=== <module> details (first 15 true_diffs) ===")
        for d in true_diffs[:15]:
            print(f"  orig: {d.get('orig_op')} {d.get('orig_arg')} | decomp: {d.get('decomp_op')} {d.get('decomp_arg')}")

# Show decompiled source
print("\n=== Decompiled source (first 80 lines) ===")
lines = source.split('\n')
for i, line in enumerate(lines[:80]):
    print(f"  {i}: {line}")
