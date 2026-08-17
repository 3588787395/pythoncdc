#!/usr/bin/env python3
"""Debug stk_resample_days_bars"""
import sys, types, marshal, dis, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

import json
with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

for entry in pyc_index:
    if os.path.basename(entry['path']) != 'history_api.pyc':
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
    
    oi = _filter_noise_instrs(get_bytecode_instructions(om['stk_resample_days_bars']))
    di = _filter_noise_instrs(get_bytecode_instructions(dm['stk_resample_days_bars']))
    
    # Check around idx 236
    for i in range(234, min(239, len(oi), len(di))):
        o = oi[i]
        d = di[i]
        print(f"  [{i}] o={o.opname:30s}({repr(o.argval)[:20]}) | d={d.opname:30s}({repr(d.argval)[:20]})")
    
    # Check what follows idx 236 in both
    print(f"\n  oi[236]={oi[236].opname}({oi[236].argval})")
    print(f"  oi[237]={oi[237].opname if 237 < len(oi) else 'NONE'}")
    print(f"  oi[238]={oi[238].opname if 238 < len(oi) else 'NONE'}")
    print(f"  di[236]={di[236].opname}({di[236].argval})")
    print(f"  di[237]={di[237].opname if 237 < len(di) else 'NONE'}")
    print(f"  di[238]={di[238].opname if 238 < len(di) else 'NONE'}")
    break
