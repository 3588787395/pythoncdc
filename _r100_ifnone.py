#!/usr/bin/env python3
"""Check POP_JUMP_IF_NONE vs POP_JUMP_IF_FALSE pattern"""
import sys, types, marshal, dis, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

import json
with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

for entry in pyc_index:
    if os.path.basename(entry['path']) != 'user_error.pyc':
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
    
    oi = _filter_noise_instrs(get_bytecode_instructions(om['get_user_error_info']))
    di = _filter_noise_instrs(get_bytecode_instructions(dm['get_user_error_info']))
    
    # Show around idx 145
    print("Around idx 145:")
    for i in range(140, min(150, len(oi), len(di))):
        o = oi[i]
        d = di[i]
        match = "OK" if o.opname == d.opname else "XX"
        print(f"  [{i}] {match} o={o.opname:35s}({repr(o.argval)[:20]:20s}) | d={d.opname:35s}({repr(d.argval)[:20]})")
    
    # Check: orig has POP_JUMP_FORWARD_IF_NONE, decomp has POP_JUMP_FORWARD_IF_FALSE
    # Both check "is this None/false?" and jump if so
    # IF_NONE checks specifically for None, IF_FALSE checks for falsy
    # When the value comes from re.match(), None is the only falsy value
    # So they're semantically equivalent in this context
    
    # Also show source
    with open(ok_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"\nSource around the pattern:")
    for i, line in enumerate(lines, 1):
        if 'regMatch' in line and ('None' in line or 'not' in line):
            print(f"  {i:3d}: {line.rstrip()[:80]}")
    break
