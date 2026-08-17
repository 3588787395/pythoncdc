#!/usr/bin/env python3
"""R100: Analyze new 1-diff functions"""
import sys, types, marshal, dis, json, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

targets = [
    ('api_data.pyc', 'get_reits_list_common'),
    ('api_data.pyc', 'check_limit_common'),
    ('ptrade_future_broker.pyc', 'process_order'),
    ('ptrade_option_broker.pyc', 'process_order'),
    ('user_error.pyc', 'get_user_error_info'),
    ('user_error.pyc', 'get_backtest_user_error_info'),
    ('finance_data_source.pyc', 'get_valuation'),
    ('history_api.pyc', 'stk_resample_days_bars'),
    ('record_store.pyc', 'add_record'),
]

for target_pyc, target_func in targets:
    for entry in pyc_index:
        if os.path.basename(entry['path']) != target_pyc:
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
        
        if target_func not in om or target_func not in dm:
            continue
        
        result = compare_bytecode(om[target_func], dm[target_func])
        oi = _filter_noise_instrs(get_bytecode_instructions(om[target_func]))
        di = _filter_noise_instrs(get_bytecode_instructions(dm[target_func]))
        
        print(f"\n=== {target_pyc}::{target_func}: diffs={len(result['true_diffs'])}, orig={len(oi)}, decomp={len(di)} ===")
        
        for diff in result['true_diffs']:
            idx = diff['index']
            start = max(0, idx - 3)
            end = min(len(oi), len(di), idx + 5)
            print(f"  Diff at idx {idx}:")
            for i in range(start, end):
                o = oi[i] if i < len(oi) else None
                d = di[i] if i < len(di) else None
                o_str = f"{o.opname}({repr(o.argval)[:25]})" if o else "NONE"
                d_str = f"{d.opname}({repr(d.argval)[:25]})" if d else "NONE"
                match = "OK" if o and d and o.opname == d.opname else "XX"
                marker = " >>>" if i == idx else "    "
                print(f"  {marker}[{i:3d}] {match} o={o_str:40s} | d={d_str}")
        break
