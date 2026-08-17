#!/usr/bin/env python3
"""R100: Analyze LOAD_GLOBAL vs LOAD_FAST pattern"""
import sys, types, marshal, dis, json, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

affected = []

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
        if not result['true_diffs']:
            continue
        
        oi = _filter_noise_instrs(get_bytecode_instructions(om[name]))
        di = _filter_noise_instrs(get_bytecode_instructions(dm[name]))
        
        first = result['true_diffs'][0]
        idx = first['index']
        
        if idx >= len(oi) or idx >= len(di):
            continue
        
        o_op = oi[idx].opname
        d_op = di[idx].opname
        len_diff = len(oi) - len(di)
        
        if abs(len_diff) <= 10:
            if o_op == 'LOAD_GLOBAL' and d_op == 'LOAD_FAST':
                affected.append((os.path.basename(pyc_path), name, oi[idx].argval, di[idx].argval, idx))
            elif o_op == 'LOAD_FAST' and d_op == 'LOAD_GLOBAL':
                affected.append((os.path.basename(pyc_path), name, oi[idx].argval, di[idx].argval, idx))

print(f"LOAD_GLOBAL vs LOAD_FAST affected functions: {len(affected)}")
for pyc, func, o_arg, d_arg, idx in affected[:15]:
    print(f"  {pyc}::{func} idx={idx}: orig=LOAD_{ 'GLOBAL' if o_arg else 'FAST'}({o_arg}), decomp=LOAD_{'FAST' if d_arg else 'GLOBAL'}({d_arg})")
