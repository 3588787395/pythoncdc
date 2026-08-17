#!/usr/bin/env python3
"""Check if the 14 failures are regressions by examining instruction diffs"""
import sys, marshal, dis, subprocess
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

fail_files = [
    'site-packages/IQCommon/backtest/backtest.pyc',
    'site-packages/IQCommon/const.pyc',
    'site-packages/IQCommon/data/api_data.pyc',
    'site-packages/IQData/plugins/plugin_system_client_db/base_db_table.pyc',
    'site-packages/fly/common/user_error.pyc',
    'site-packages/fly/data/quotation.pyc',
    'site-packages/IQEngine/core/bar.pyc',
    'site-packages/IQEngine/utils/trade_schedule.pyc',
]

for pyc_path in fail_files:
    full_path = f'F:/Downloads/pythoncdc-main/{pyc_path}'
    py_path = full_path.replace('.pyc', 'OK.py')
    if not Path(py_path).exists():
        print(f"  {pyc_path}: no output file")
        continue
    
    with open(full_path, 'rb') as f:
        f.read(16)
        orig_code = marshal.loads(f.read())
    
    source = Path(py_path).read_text(encoding='utf-8')
    try:
        decomp_code = compile(source, py_path, 'exec')
    except SyntaxError as e:
        print(f"  {pyc_path}: syntax error: {e}")
        continue
    
    orig_instrs = list(dis.get_instructions(orig_code))
    decomp_instrs = list(dis.get_instructions(decomp_code))
    
    # Find first diff
    min_len = min(len(orig_instrs), len(decomp_instrs))
    first_diff = None
    for i in range(min_len):
        o = orig_instrs[i]
        d = decomp_instrs[i]
        if o.opname != d.opname:
            first_diff = f"idx={i}: orig={o.offset}:{o.opname}:{o.argval} decomp={d.offset}:{d.opname}:{d.argval}"
            break
    
    print(f"  {pyc_path.split('/')[-1]}: {len(orig_instrs)} vs {len(decomp_instrs)} (diff={len(decomp_instrs)-len(orig_instrs)})")
    if first_diff:
        print(f"    First diff: {first_diff}")
