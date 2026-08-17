#!/usr/bin/env python3
"""R100: Analyze after_jump_forward_mismatch pattern"""
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
            prev_o = oi[idx-1].opname if idx > 0 else 'START'
            prev_d = di[idx-1].opname if idx > 0 else 'START'
            
            if prev_o == 'JUMP_FORWARD' and prev_d != 'JUMP_FORWARD':
                # The orig has JUMP_FORWARD but decomp has something else
                affected.append((os.path.basename(pyc_path), name, idx, 
                                 o_op, d_op, 
                                 oi[idx-1].argval if idx > 0 else None,
                                 di[idx-1].argval if idx > 0 else None))

print(f"after_jump_forward_mismatch: {len(affected)}")
for pyc, func, idx, o_op, d_op, o_arg, d_arg in affected[:15]:
    print(f"  {pyc}::{func} idx={idx}: orig={o_op}, decomp={d_op}")
    print(f"    prev orig: JUMP_FORWARD({o_arg}), prev decomp: {d_arg}")
