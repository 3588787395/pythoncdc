import sys, types, marshal, io, dis, os, json
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode
from pycdc import decompile_pyc

# Load pyc_index
with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Collect first-diff patterns across ALL partial files
pattern_counts = {}
file_patterns = {}

for idx, entry in enumerate(data):
    if entry.get('decompile_status') != 'partial':
        continue
    path = entry.get('path', '')
    basename = os.path.basename(path)
    
    try:
        with open(path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        source = decompile_pyc(path)
        decomp_code = compile(source, '<decompiled>', 'exec')
    except Exception as e:
        continue
    
    def extract_code_objects(code, prefix=''):
        result = {prefix or code.co_name: code}
        for const in code.co_consts:
            if isinstance(const, types.CodeType):
                result.update(extract_code_objects(const, f"{prefix}.{const.co_name}" if prefix else const.co_name))
        return result
    
    orig_map = extract_code_objects(orig_code)
    decomp_map = extract_code_objects(decomp_code)
    
    common = set(orig_map.keys()) & set(decomp_map.keys())
    file_mismatch_count = 0
    
    for name in sorted(common):
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if not cmp.get('match') and not cmp.get('jump_only'):
            file_mismatch_count += 1
            true_diffs = cmp.get('true_diffs', [])
            if true_diffs:
                first = true_diffs[0]
                orig_op = first.get('orig_op', '?')
                decomp_op = first.get('decomp_op', '?')
                # Classify pattern
                if orig_op == decomp_op:
                    pattern = f"SAME_OP:{orig_op}"
                else:
                    pattern = f"{orig_op}->{decomp_op}"
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
    
    if file_mismatch_count > 0:
        file_patterns[basename] = file_mismatch_count

print("=== Top 20 most common first-diff patterns ===")
for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1])[:20]:
    print(f"  {pattern}: {count}")

print(f"\nTotal mismatched functions: {sum(pattern_counts.values())}")
print(f"Total partial files with mismatches: {len(file_patterns)}")
