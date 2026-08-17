#!/usr/bin/env python3
"""Debug: test _trim_except_branch_return_none directly"""
import sys, types, marshal, dis, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import get_bytecode_instructions, _filter_noise_instrs

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
        
        orig = _filter_noise_instrs(get_bytecode_instructions(om['_get_manage_info']))
        decomp = _filter_noise_instrs(get_bytecode_instructions(dm['_get_manage_info']))
        
        # Simulate _trim_spurious_intermediate_returns (no-op for this case)
        # Then simulate _trim_except_branch_return_none
        trim_positions = set()
        for i in range(len(decomp) - 1):
            if (decomp[i].opname == 'LOAD_CONST'
                    and decomp[i].argval is None
                    and decomp[i + 1].opname == 'RETURN_VALUE'):
                if i < len(orig) and orig[i].opname == 'JUMP_FORWARD':
                    if i + 1 < len(orig) and orig[i + 1].opname == 'RERAISE':
                        trim_positions.add(i)
                        print(f"Found trim position at idx {i}: decomp={decomp[i].opname}({decomp[i].argval}), orig={orig[i].opname}")
        
        print(f"Trim positions: {trim_positions}")
        
        if trim_positions:
            result = []
            i = 0
            while i < len(decomp):
                if i in trim_positions:
                    i += 2
                else:
                    result.append(decomp[i])
                    i += 1
            
            print(f"\nAfter trim: {len(result)} instrs (was {len(decomp)})")
            for i, ins in enumerate(result):
                o = orig[i] if i < len(orig) else None
                match = "OK" if o and ins.opname == o.opname else "XX"
                print(f"  [{i:2d}] {match} o={o.opname if o else 'NONE':30s} | d={ins.opname}")
        
        break
