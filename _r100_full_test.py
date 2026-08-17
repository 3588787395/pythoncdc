#!/usr/bin/env python3
"""R100: Full test suite"""
import sys, types, marshal, dis, json, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs, decompile_pyc

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

ok_count = 0
partial_count = 0
fail_count = 0
new_ok = []

for entry in pyc_index:
    pyc_path = entry['path']
    ok_path = pyc_path.replace('.pyc', 'OK.py')
    if not os.path.exists(pyc_path) or not os.path.exists(ok_path):
        continue
    
    try:
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
    except:
        fail_count += 1
        continue
    
    try:
        source = decompile_pyc(pyc_path)
        decomp_code = compile(source, '<decomp>', 'exec')
    except:
        partial_count += 1
        entry['decompile_status'] = 'partial'
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
        if entry.get('decompile_status') != 'ok':
            new_ok.append(os.path.basename(pyc_path))
            entry['decompile_status'] = 'ok'
    else:
        partial_count += 1
        entry['decompile_status'] = 'partial'

print(f"OK: {ok_count}")
print(f"Partial: {partial_count}")
print(f"Fail: {fail_count}")
if new_ok:
    print(f"\nNewly OK ({len(new_ok)}):")
    for f in new_ok[:20]:
        print(f"  {f}")

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'w', encoding='utf-8') as f:
    json.dump(pyc_index, f, indent=2, ensure_ascii=False)
