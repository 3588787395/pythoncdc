#!/usr/bin/env python3
"""R100: Analyze CONTAINS_OP(0) vs CONTAINS_OP(1) pattern"""
import sys, types, marshal, dis, json, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

# Check convert.pyc::getchnstr more carefully
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
    
    oi = _filter_noise_instrs(get_bytecode_instructions(om['getchnstr']))
    di = _filter_noise_instrs(get_bytecode_instructions(dm['getchnstr']))
    
    print("Full getchnstr comparison:")
    for i in range(min(len(oi), len(di))):
        o = oi[i]
        d = di[i]
        match = "OK" if o.opname == d.opname else "XX"
        # Also check argval
        if match == "OK" and o.argval != d.argval:
            match = "~~"
        print(f"  [{i:3d}] {match} o={o.opname:35s}({repr(o.argval)[:20]:20s}) | d={d.opname:35s}({repr(d.argval)[:20]})")
    
    # Show source
    print(f"\nDecompiled source:")
    with open(ok_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f.readlines(), 1):
            if 'getchnstr' in line or 'CONTAINS' in line or 'in ' in line or 'not in' in line:
                print(f"  {i:3d}: {line.rstrip()[:80]}")
    break
