#!/usr/bin/env python3
"""Check all functions in trade_schedule.pyc"""

import sys, os, marshal, types, dis

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PYC_PATH = os.path.join(HERE, 'site-packages', 'IQData', 'utils', 'trade_schedule.pyc')

with open(PYC_PATH, 'rb') as f:
    magic = f.read(4)
    f.read(12)  # flags + timestamp + size
    code = marshal.load(f)

def list_code_objects(code_obj, prefix=''):
    results = []
    name = prefix + code_obj.co_name if prefix else code_obj.co_name
    if name == '<module>':
        name = '<module>'
    results.append((name, code_obj))
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            sub_prefix = name + '.' if name != '<module>' else ''
            results.extend(list_code_objects(const, sub_prefix))
    return results

all_codes = list_code_objects(code)
print(f"Total code objects: {len(all_codes)}")
for name, co in all_codes:
    print(f"  {name} (argcount={co.co_argcount}, nlocals={co.co_nlocals}, instructions={len(list(dis.get_instructions(co)))})")
