#!/usr/bin/env python3
"""R100: Analyze different_op_small_diff pattern in detail"""
import sys, types, marshal, dis, json, os
from collections import Counter
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

op_pairs = Counter()

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
        
        if o_op != d_op and abs(len_diff) <= 10:
            # This is the different_op_small_diff pattern
            # Check what comes before
            prev_o = oi[idx-1].opname if idx > 0 else 'START'
            prev_d = di[idx-1].opname if idx > 0 else 'START'
            
            # Check if prev is JUMP_FORWARD in orig but not in decomp
            # (indicates code block ordering issue after a jump)
            if prev_o == 'JUMP_FORWARD' and prev_d != 'JUMP_FORWARD':
                op_pairs['after_jump_forward_mismatch'] += 1
            elif prev_o == 'POP_TOP' and prev_d == 'POP_TOP':
                op_pairs['after_pop_top'] += 1
            else:
                op_pairs[f'{o_op}_vs_{d_op}'] += 1

print("Op pair patterns (different_op_small_diff):")
for pair, count in op_pairs.most_common(20):
    print(f"  {pair}: {count}")
