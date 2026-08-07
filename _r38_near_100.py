"""R38: Find and analyze files closest to 100% match rate"""
import json, sys, os, marshal, types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from testqouter.round1.base import decompile_pyc, compare_bytecode

idx = json.load(open('pyc_index.json', 'r', encoding='utf-8'))
not_ok = [e for e in idx if e['decompile_status'] != 'ok']
not_ok.sort(key=lambda x: x['bytecode_match_rate'], reverse=True)

# Check top 15 files closest to 100%
for entry in not_ok[:15]:
    pyc_path = entry['path']
    short = pyc_path.split('site-packages/')[-1]
    rate = entry['bytecode_match_rate']
    funcs = entry['function_count']
    unmatched = funcs - int(funcs * rate)
    
    if unmatched > 3:
        continue
    
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
        
        mismatches = []
        for name, orig_fc in orig_funcs.items():
            if name not in decomp_funcs:
                continue
            result = compare_bytecode(orig_fc, decomp_funcs[name])
            if result['match'] or result.get('jump_only'):
                continue
            td = result['true_diffs']
            jd = result['jump_diffs']
            if td:
                first = td[0]
                mismatches.append(f"  {name}: td={len(td)} jd={len(jd)} first={first.get('orig_op')}({first.get('orig_arg')}) vs {first.get('decomp_op')}({first.get('decomp_arg')})")
            elif jd:
                mismatches.append(f"  {name}: jd={len(jd)} only")
        
        if mismatches:
            print(f"\n{short}: {rate:.2%} ({funcs} funcs, {unmatched} unmatched)")
            for m in mismatches[:3]:
                print(m)
    except Exception as e:
        print(f"\n{short}: ERROR {e}")
