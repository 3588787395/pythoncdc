#!/usr/bin/env python3
"""R100: Verify compare_bytecode for getchnstr"""
import sys, types, marshal, dis, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

import json
with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

for entry in pyc_index:
    if os.path.basename(entry['path']) != 'convert.pyc':
        continue
    pyc_path = entry['path']
    ok_path = pyc_path.replace('.pyc', 'OK.py')
    if not os.path.exists(ok_path):
        continue
    with open(pyc_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.load(f)
    with open(ok_path, 'r', encoding='utf-8') as f:
        source = f.read()
    decomp_code = compile(source, ok_path, 'exec')
    
    def extract(co):
        r = {co.co_name: co}
        for c in co.co_consts:
            if isinstance(c, types.CodeType):
                r.update(extract(c))
        return r
    
    om = extract(orig_code)
    dm = extract(decomp_code)
    
    result = compare_bytecode(om['getchnstr'], dm['getchnstr'])
    print(f"getchnstr: match={result['match']}, diffs={len(result['true_diffs'])}, jump_diffs={len(result['jump_diffs'])}")
    for d in result['true_diffs']:
        print(f"  true_diff: {d}")
    for d in result['jump_diffs']:
        print(f"  jump_diff: {d}")
    break
