"""R37: Analyze common mismatch patterns across top partial files"""
import json, sys, os, marshal, types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from testqouter.round1.base import decompile_pyc, compare_bytecode

idx = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
not_ok = [e for e in idx if e['decompile_status'] != 'ok']
for e in not_ok:
    e['unmatched'] = e['function_count'] * (1 - e['bytecode_match_rate'])
not_ok.sort(key=lambda x: x['unmatched'], reverse=True)

# Analyze top 10 files
pattern_counts = {}
total_mismatches = 0

for entry in not_ok[:10]:
    pyc_path = entry['path']
    short = pyc_path.split('site-packages/')[-1]
    
    try:
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        
        source = decompile_pyc(pyc_path)
        decomp_code = compile(source, '<decompiled>', 'exec')
        
        def extract_codes(code, prefix=""):
            result = {prefix + code.co_name: code}
            for c in code.co_consts:
                if isinstance(c, types.CodeType):
                    result.update(extract_codes(c, prefix + code.co_name + "."))
            return result
        
        orig_funcs = extract_codes(orig_code)
        decomp_funcs = extract_codes(decomp_code)
        
        file_mismatches = 0
        for name, orig_fc in orig_funcs.items():
            if name not in decomp_funcs:
                continue
            result = compare_bytecode(orig_fc, decomp_funcs[name])
            if result['match'] or result.get('jump_only'):
                continue
            
            file_mismatches += 1
            total_mismatches += 1
            td = result['true_diffs']
            
            for d in td[:3]:  # First 3 diffs per function
                orig_op = d.get('orig_op', '?')
                decomp_op = d.get('decomp_op', '?')
                pattern = f"{orig_op} vs {decomp_op}"
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        print(f"  {short}: {file_mismatches} mismatches")
    except Exception as e:
        print(f"  {short}: ERROR {e}")

print(f"\nTotal mismatches in top 10 files: {total_mismatches}")
print(f"\n=== Top 20 mismatch patterns ===")
sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
for pattern, count in sorted_patterns[:20]:
    print(f"  {count:4d}  {pattern}")
