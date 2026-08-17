#!/usr/bin/env python3
"""Debug: check if _trim_except_branch_return_none is working"""
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
        
        oi = _filter_noise_instrs(get_bytecode_instructions(om['_get_manage_info']))
        di_raw = _filter_noise_instrs(get_bytecode_instructions(dm['_get_manage_info']))
        
        # Manually check the pattern
        print("Raw decomp instructions:")
        for i, ins in enumerate(di_raw):
            print(f"  [{i:2d}] {ins.opname:30s} argval={repr(ins.argval)[:20]}")
        
        print(f"\nOrig instructions:")
        for i, ins in enumerate(oi):
            print(f"  [{i:2d}] {ins.opname:30s} argval={repr(ins.argval)[:20]}")
        
        # Check the pattern manually
        for i in range(len(di_raw) - 1):
            if di_raw[i].opname == 'LOAD_CONST' and di_raw[i].argval is None:
                if di_raw[i+1].opname == 'RETURN_VALUE':
                    if i < len(oi) and oi[i].opname == 'JUMP_FORWARD':
                        if i+1 < len(oi) and oi[i+1].opname == 'RERAISE':
                            print(f"\nPattern found at idx {i}!")
        
        # Now call compare_bytecode
        result = compare_bytecode(om['_get_manage_info'], dm['_get_manage_info'])
        print(f"\nResult: match={result['match']}, diffs={len(result['true_diffs'])}")
        break
