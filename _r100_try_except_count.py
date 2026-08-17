#!/usr/bin/env python3
"""R100: Count functions with JUMP_FORWARD vs RERAISE pattern"""
import sys, types, marshal, dis, json, os
from collections import Counter
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

count = 0
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
        
        # Check for try/except related patterns
        if o_op == 'JUMP_FORWARD' and d_op == 'LOAD_CONST':
            if idx + 1 < len(di) and di[idx+1].opname == 'RETURN_VALUE':
                if idx + 1 < len(oi) and oi[idx+1].opname == 'RERAISE':
                    count += 1
                    affected.append((os.path.basename(pyc_path), name, idx, len(oi), len(di)))
                elif idx + 1 < len(oi) and oi[idx+1].opname in ('COPY', 'POP_EXCEPT'):
                    count += 1
                    affected.append((os.path.basename(pyc_path), name, idx, len(oi), len(di)))

# Also check the reverse: orig has RERAISE where decomp has something else
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
        
        # Check for PUSH_EXC_INFO vs RETURN_VALUE pattern
        for diff in result['true_diffs'][:1]:
            idx = diff['index']
            if idx >= len(oi) or idx >= len(di):
                continue
            if oi[idx].opname == 'PUSH_EXC_INFO' and di[idx].opname == 'RETURN_VALUE':
                if (os.path.basename(pyc_path), name) not in [(a[0], a[1]) for a in affected]:
                    count += 1
                    affected.append((os.path.basename(pyc_path), name, idx, len(oi), len(di)))

print(f"Try/except related diff functions: {len(affected)}")
for pyc, func, idx, oi_len, di_len in affected[:20]:
    print(f"  {pyc}::{func} idx={idx} orig={oi_len} decomp={di_len}")
