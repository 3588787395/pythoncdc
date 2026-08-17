#!/usr/bin/env python3
"""R100: Check bytecode alignment around the problematic area"""
import sys, types, marshal, dis, os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.path.insert(0, 'f:/Downloads/pythoncdc-main/testqouter/round1')
from base import compare_bytecode, get_bytecode_instructions, _filter_noise_instrs

import json
with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

for entry in pyc_index:
    if 'api_base' in entry['path'] and entry['path'].endswith('.pyc') and 'IQData' in entry['path']:
        pyc_path = entry['path']
        break

ok_path = pyc_path.replace('.pyc', 'OK.py')
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

oi = _filter_noise_instrs(get_bytecode_instructions(om['get_history_df']))
di = _filter_noise_instrs(get_bytecode_instructions(dm['get_history_df']))

# Find the area around offset 1034-1200 in original
print("Original instrs around offset 1024-1210:")
for ins in oi:
    if 1020 <= ins.offset <= 1210:
        print(f"  {ins.offset:4d} {ins.opname:35s} {ins.argrepr[:40]}")

print("\nDecompiled instrs around same area:")
# Find the equivalent area in decompiled
for i, ins in enumerate(di):
    # Look for the pattern: LOAD_FAST pm_open_market_datetime + COMPARE_OP
    if ins.opname == 'LOAD_FAST' and ins.argval == 'pm_open_market_datetime':
        # Show surrounding instructions
        start = max(0, i - 2)
        end = min(len(di), i + 40)
        for j in range(start, end):
            d = di[j]
            print(f"  [{j:4d}] {d.offset:4d} {d.opname:35s} {d.argrepr[:40]}")
        break
