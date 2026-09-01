import sys, json, marshal, types, dis, os, py_compile, importlib.util
sys.path.insert(0, '.')
from testqouter.round1.base import compare_bytecode, _filter_noise_instrs
from collections import Counter

def _load_pyc_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def _extract_code_objects(code, prefix=''):
    result = {}
    key = prefix + code.co_name
    if key in result:
        key = key + f'_{id(code)}'
    result[key] = code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(_extract_code_objects(const, prefix + code.co_name + '.'))
    return result

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

pattern_counter = Counter()
pattern_examples = {}
total_mismatches = 0
file_mismatch_counts = Counter()

for entry in index:
    if entry.get('decompile_status') != 'partial':
        continue
    pyc_path = entry['path']
    ok_py_path = pyc_path[:-4] + 'OK.py'
    
    try:
        orig_code = _load_pyc_code(pyc_path)
    except:
        continue
    
    if not os.path.exists(ok_py_path):
        continue
    
    try:
        cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
        if cfile is None:
            cfile = importlib.util.cache_from_source(ok_py_path)
    except:
        continue
    
    try:
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
    except:
        continue
    
    orig_map = _extract_code_objects(orig_code)
    decomp_map = _extract_code_objects(decomp_code)
    
    orig_names = set(orig_map.keys())
    decomp_names = set(decomp_map.keys())
    common = orig_names & decomp_names
    
    file_count = 0
    for name in sorted(common):
        details = compare_bytecode(orig_map[name], decomp_map[name])
        if details.get('match') or details.get('jump_only'):
            continue
        
        true_diffs = details.get('true_diffs', [])
        if not true_diffs:
            continue
        
        total_mismatches += 1
        file_count += 1
        first_diff = true_diffs[0]
        orig_op = first_diff.get('orig_op')
        decomp_op = first_diff.get('decomp_op')
        
        if orig_op and decomp_op:
            key_str = f"{orig_op} -> {decomp_op}"
            pattern_counter[key_str] += 1
            if key_str not in pattern_examples or pattern_counter[key_str] <= 3:
                idx = first_diff.get('index', 0)
                orig_filtered = _filter_noise_instrs(list(dis.get_instructions(orig_map[name])))
                decomp_filtered = _filter_noise_instrs(list(dis.get_instructions(decomp_map[name])))
                
                orig_ctx = [(i.opname, getattr(i, 'argval', None)) for i in orig_filtered[max(0,idx-3):idx+5]]
                decomp_ctx = [(i.opname, getattr(i, 'argval', None)) for i in decomp_filtered[max(0,idx-3):idx+5]]
                
                pattern_examples[key_str] = {
                    'func': name,
                    'file': pyc_path.split('site-packages')[-1] if 'site-packages' in pyc_path else pyc_path,
                    'orig_idx': idx,
                    'orig_ctx': orig_ctx,
                    'decomp_ctx': decomp_ctx,
                    'total_orig': len(orig_filtered),
                    'total_decomp': len(decomp_filtered),
                    'true_diffs_count': len(true_diffs),
                }
    
    if file_count > 0:
        short = pyc_path.split('site-packages')[-1] if 'site-packages' in pyc_path else pyc_path
        file_mismatch_counts[short] = file_count

print(f"Total mismatched functions with true_diffs: {total_mismatches}")
print(f"\nTop patterns:")
for pat, count in pattern_counter.most_common(25):
    ex = pattern_examples[pat]
    print(f"\n  {count}x {pat}")
    print(f"    example: {ex['func']} in {ex['file']}")
    print(f"    orig[{ex['orig_idx']}]: {ex['orig_ctx']}")
    print(f"    decomp[{ex['orig_idx']}]: {ex['decomp_ctx']}")
    print(f"    instr counts: orig={ex['total_orig']}, decomp={ex['total_decomp']}, true_diffs={ex['true_diffs_count']}")

print(f"\n\nFiles with most mismatches:")
for f, c in file_mismatch_counts.most_common(15):
    print(f"  {c}x {f}")
