#!/usr/bin/env python3
"""R100: Count common diff patterns across all partial pyc"""
import sys, types, marshal, dis, json, os
from collections import Counter
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

# For each partial pyc, check what the first diff pattern is
patterns = Counter()
total_checked = 0

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
            patterns['index_out_of_range'] += 1
            continue
        
        o_op = oi[idx].opname
        d_op = di[idx].opname
        
        # Categorize
        len_diff = len(oi) - len(di)
        
        if abs(len_diff) <= 2 and o_op == d_op:
            # Same opcode but different arg - likely offset/ordering issue
            if o_op in ('JUMP_FORWARD', 'JUMP_BACKWARD'):
                patterns['same_op_jump_different_target'] += 1
            elif o_op in ('LOAD_CONST',):
                patterns['same_op_load_const_different'] += 1
            else:
                patterns['same_op_different_arg'] += 1
        elif o_op != d_op:
            if len_diff > 10:
                patterns['different_op_large_loss'] += 1
            elif len_diff < -10:
                patterns['different_op_large_gain'] += 1
            else:
                patterns['different_op_small_diff'] += 1
        else:
            patterns['other'] += 1
        
        total_checked += 1

print(f"Total functions checked: {total_checked}")
print(f"\nDiff patterns:")
for pattern, count in patterns.most_common():
    print(f"  {pattern}: {count}")
