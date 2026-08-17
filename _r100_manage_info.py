#!/usr/bin/env python3
"""R100: Analyze _get_manage_info try/except issue"""
import sys, types, marshal, dis, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

import json
with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

for entry in pyc_index:
    if 'instance' in entry['path'] and entry['path'].endswith('.pyc'):
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
        
        if '_get_manage_info' not in om:
            continue
        
        result = compare_bytecode(om['_get_manage_info'], dm['_get_manage_info'])
        oi = _filter_noise_instrs(get_bytecode_instructions(om['_get_manage_info']))
        di = _filter_noise_instrs(get_bytecode_instructions(dm['_get_manage_info']))
        
        print(f"_get_manage_info: orig={len(oi)}, decomp={len(di)}, diffs={len(result['true_diffs'])}")
        
        # Show context around first diff
        first = result['true_diffs'][0]
        idx = first['index']
        start = max(0, idx - 10)
        end = min(len(oi), len(di), idx + 15)
        
        print(f"\nContext around first diff (idx={idx}):")
        for i in range(start, end):
            o = oi[i] if i < len(oi) else None
            d = di[i] if i < len(di) else None
            o_str = f"{o.opname}({repr(o.argval)[:25]})" if o else "NONE"
            d_str = f"{d.opname}({repr(d.argval)[:25]})" if d else "NONE"
            match = "OK" if o and d and o.opname == d.opname else "XX"
            marker = " >>>" if i == idx else "    "
            print(f"  {marker}[{i:3d}] {match} o={o_str:40s} | d={d_str}")
        break
