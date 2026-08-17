#!/usr/bin/env python3
"""R100: Analyze get_history_df - high diffs but small len_diff"""
import sys, types, marshal, dis, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

# Find api_base.pyc in IQData
import json
with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

for entry in pyc_index:
    if 'api_base' in entry['path'] and entry['path'].endswith('.pyc'):
        pyc_path = entry['path']
        ok_path = pyc_path.replace('.pyc', 'OK.py')
        if not os.path.exists(ok_path):
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
        
        if 'get_history_df' not in om:
            continue
        
        result = compare_bytecode(om['get_history_df'], dm['get_history_df'])
        oi = _filter_noise_instrs(get_bytecode_instructions(om['get_history_df']))
        di = _filter_noise_instrs(get_bytecode_instructions(dm['get_history_df']))
        
        print(f"get_history_df: orig={len(oi)}, decomp={len(di)}, diffs={len(result['true_diffs'])}")
        
        # Show first diff context
        first = result['true_diffs'][0]
        idx = first['index']
        print(f"\nFirst diff at idx {idx}")
        
        start = max(0, idx - 3)
        end = min(len(oi), len(di), idx + 15)
        for i in range(start, end):
            o = oi[i] if i < len(oi) else None
            d = di[i] if i < len(di) else None
            o_str = f"{o.opname}({repr(o.argval)[:25]})" if o else "NONE"
            d_str = f"{d.opname}({repr(d.argval)[:25]})" if d else "NONE"
            match = "OK" if o and d and o.opname == d.opname else "XX"
            marker = " >>>" if i == idx else "    "
            print(f"  {marker}[{i}] {match} o={o_str} | d={d_str}")
        
        # Check: is it a constant tuple ordering issue?
        # Look for LOAD_CONST with tuple values
        const_diffs = 0
        for diff in result['true_diffs']:
            i = diff['index']
            if i < len(oi) and i < len(di):
                if oi[i].opname == di[i].opname == 'LOAD_CONST':
                    if oi[i].argval != di[i].argval:
                        const_diffs += 1
        print(f"\nLOAD_CONST value mismatches: {const_diffs}")
        
        # Check for JUMP_FORWARD vs RETURN_VALUE pattern
        jump_vs_return = 0
        for diff in result['true_diffs']:
            i = diff['index']
            if i < len(oi) and i < len(di):
                if oi[i].opname == 'JUMP_FORWARD' and di[i].opname == 'RETURN_VALUE':
                    jump_vs_return += 1
                elif oi[i].opname == 'RETURN_VALUE' and di[i].opname == 'JUMP_FORWARD':
                    jump_vs_return += 1
        print(f"JUMP_FORWARD vs RETURN_VALUE: {jump_vs_return}")
        break
