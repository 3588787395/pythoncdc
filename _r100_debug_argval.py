#!/usr/bin/env python3
"""Debug: check what argval is for LOAD_CONST(None)"""
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
        with open(ok_path, 'r', encoding='utf-8') as f:
            source = f.read()
        decomp_code = compile(source, ok_path, 'exec')
        
        def extract(co):
            r = {co.co_name: co}
            for c in co.co_consts:
                if isinstance(c, types.CodeType):
                    r.update(extract(c))
            return r
        
        dm = extract(decomp_code)
        di = _filter_noise_instrs(get_bytecode_instructions(dm['_get_manage_info']))
        
        # Check idx 19
        ins = di[19]
        print(f"idx 19: opname={ins.opname}, argval={repr(ins.argval)}, type={type(ins.argval)}")
        print(f"  argval is None: {ins.argval is None}")
        print(f"  argval == None: {ins.argval == None}")
        break
