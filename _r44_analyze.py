import sys, types, marshal, io, dis, os, json
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode, _filter_noise_instrs
from pycdc import decompile_pyc

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def extract_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const, f"{prefix}.{const.co_name}" if prefix else const.co_name))
    return result

pattern_counts = {}

for entry in data:
    if entry.get('decompile_status') != 'partial':
        continue
    path = entry.get('path', '')
    
    try:
        with open(path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        source = decompile_pyc(path)
        decomp_code = compile(source, '<decompiled>', 'exec')
    except:
        continue
    
    orig_map = extract_code_objects(orig_code)
    decomp_map = extract_code_objects(decomp_code)
    
    for name in sorted(orig_map.keys()):
        if name in decomp_map:
            cmp = compare_bytecode(orig_map[name], decomp_map[name])
            if not cmp.get('match') and not cmp.get('jump_only'):
                true_diffs = cmp.get('true_diffs', [])
                if true_diffs:
                    first = true_diffs[0]
                    orig_op = first.get('orig_op', '?')
                    decomp_op = first.get('decomp_op', '?')
                    if orig_op == decomp_op:
                        pattern = f"SAME_OP:{orig_op}"
                    else:
                        pattern = f"{orig_op}->{decomp_op}"
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

print("=== Top 20 most common first-diff patterns (R43 post-fix) ===")
for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1])[:20]:
    print(f"  {pattern}: {count}")

total_mismatched = sum(pattern_counts.values())
print(f"\nTotal mismatched functions: {total_mismatched}")
