import sys, types, marshal, io, dis, os, json
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')
from base import compare_bytecode
from pycdc import decompile_pyc

# Load pyc_index to find low match rate files
with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Get partial files sorted by match rate (lowest first)
partials = []
for entry in data:
    if entry.get('decompile_status') == 'partial':
        rate = entry.get('bytecode_match_rate', 0.0)
        path = entry.get('path', '')
        partials.append((rate, path))

partials.sort()

# Analyze the lowest 10 files
def extract_code_objects(code, prefix=''):
    result = {prefix or code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const, f"{prefix}.{const.co_name}" if prefix else const.co_name))
    return result

print("=== Common failure patterns in lowest match rate files ===\n")
pattern_counts = {}

for rate, path in partials[:10]:
    basename = os.path.basename(path)
    print(f"\n--- {basename} ({rate*100:.2f}%) ---")
    
    try:
        with open(path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        orig_map = extract_code_objects(orig_code)
        
        source = decompile_pyc(path)
        decomp_code = compile(source, '<decompiled>', 'exec')
        decomp_map = extract_code_objects(decomp_code)
    except Exception as e:
        print(f"  Error: {e}")
        continue
    
    common = set(orig_map.keys()) & set(decomp_map.keys())
    missing = set(orig_map.keys()) - set(decomp_map.keys())
    extra = set(decomp_map.keys()) - set(orig_map.keys())
    
    mismatch_count = 0
    for name in sorted(common):
        cmp = compare_bytecode(orig_map[name], decomp_map[name])
        if not cmp.get('match') and not cmp.get('jump_only'):
            mismatch_count += 1
            true_diffs = cmp.get('true_diffs', [])
            if true_diffs:
                first = true_diffs[0]
                orig_op = first.get('orig_op', '?')
                decomp_op = first.get('decomp_op', '?')
                pattern = f"{orig_op} vs {decomp_op}"
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                if mismatch_count <= 3:
                    print(f"  {name}: {pattern} (true_diffs={len(true_diffs)})")
    
    if missing:
        print(f"  Missing in decomp: {len(missing)}")
    if extra:
        print(f"  Extra in decomp: {len(extra)}")
    print(f"  Total mismatches: {mismatch_count}/{len(common)}")

print("\n\n=== Most common first-diff patterns ===")
for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1])[:15]:
    print(f"  {pattern}: {count} occurrences")
