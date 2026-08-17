#!/usr/bin/env python3
"""R101: Analyze remaining 1-5 diff functions"""
import sys, types, marshal, dis, json, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

small_diffs = []

for entry in pyc_index:
    if entry.get('decompile_status') != 'partial':
        continue
    pyc_path = entry['path']
    ok_path = pyc_path.replace('.pyc', 'OK.py')
    if not os.path.exists(pyc_path) or not os.path.exists(ok_path):
        continue
    try:
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        with open(ok_path, 'r', encoding='utf-8') as f:
            source = f.read()
        decomp_code = compile(source, ok_path, 'exec')
    except:
        continue
    
    def extract(co):
        r = {co.co_name: co}
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                r.update(extract(c))
        return r
    
    om = extract(orig_code)
    dm = extract(decomp_code)
    
    for name in om:
        if name not in dm or name.startswith('<'):
            continue
        result = compare_bytecode(om[name], dm[name])
        diffs = len(result['true_diffs'])
        if 1 <= diffs <= 10:
            oi = _filter_noise_instrs(get_bytecode_instructions(om[name]))
            di = _filter_noise_instrs(get_bytecode_instructions(dm[name]))
            small_diffs.append((os.path.basename(pyc_path), name, diffs, len(oi), len(di)))

print(f"Functions with 1-10 diffs: {len(small_diffs)}")
for pyc, func, diffs, oi, di in sorted(small_diffs, key=lambda x: x[2])[:40]:
    print(f"  {pyc}::{func}: diffs={diffs}, orig={oi}, decomp={di}")
