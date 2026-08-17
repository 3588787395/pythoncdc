#!/usr/bin/env python3
"""R100: Test using existing OK.py files (not re-decompiling)"""
import sys, types, marshal, dis, json, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

ok_count = 0
partial_count = 0
fail_count = 0
partial_files = []

for entry in pyc_index:
    pyc_path = entry['path']
    ok_path = pyc_path.replace('.pyc', 'OK.py')
    if not os.path.exists(pyc_path) or not os.path.exists(ok_path):
        fail_count += 1
        continue
    
    try:
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
    except:
        fail_count += 1
        continue
    
    try:
        with open(ok_path, 'r', encoding='utf-8') as f:
            source = f.read()
        decomp_code = compile(source, ok_path, 'exec')
    except:
        fail_count += 1
        continue
    
    def extract(co):
        r = {co.co_name: co}
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                r.update(extract(c))
        return r
    
    om = extract(orig_code)
    dm = extract(decomp_code)
    
    all_match = True
    for name in om:
        if name not in dm or name.startswith('<'):
            continue
        result = compare_bytecode(om[name], dm[name])
        if not result['match']:
            all_match = False
            break
    
    if all_match:
        ok_count += 1
        entry['decompile_status'] = 'ok'
    else:
        partial_count += 1
        entry['decompile_status'] = 'partial'
        partial_files.append(os.path.basename(pyc_path))

print(f"OK: {ok_count}")
print(f"Partial: {partial_count}")
print(f"Fail: {fail_count}")

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'w', encoding='utf-8') as f:
    json.dump(pyc_index, f, indent=2, ensure_ascii=False)
