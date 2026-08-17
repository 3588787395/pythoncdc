#!/usr/bin/env python3
"""R101: Check trailing return None patterns"""
import sys, types, marshal, dis, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

import json
with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

# Check trading_dates_reload
for entry in pyc_index:
    if os.path.basename(entry['path']) != 'trading_dates_mixin.pyc':
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
    
    oi = _filter_noise_instrs(get_bytecode_instructions(om['trading_dates_reload']))
    di = _filter_noise_instrs(get_bytecode_instructions(dm['trading_dates_reload']))
    
    print(f"trading_dates_reload: orig={len(oi)}, decomp={len(di)}")
    print("\nOrig:")
    for i, ins in enumerate(oi):
        print(f"  [{i:2d}] {ins.opname:35s} {repr(ins.argval)[:20]}")
    print("\nDecomp:")
    for i, ins in enumerate(di):
        print(f"  [{i:2d}] {ins.opname:35s} {repr(ins.argval)[:20]}")
    break
