#!/usr/bin/env python3
"""Check all trade_schedule.pyc files for their code objects."""

import sys, os, marshal, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PYC_FILES = [
    os.path.join(HERE, 'site-packages', 'IQCommon', 'trade_schedule.pyc'),
    os.path.join(HERE, 'site-packages', 'IQData', 'utils', 'trade_schedule.pyc'),
    os.path.join(HERE, 'site-packages', 'IQEngine', 'utils', 'trade_schedule.pyc'),
]

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

for pyc_path in PYC_FILES:
    if not os.path.exists(pyc_path):
        print(f"NOT FOUND: {pyc_path}")
        continue
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    all_codes = list_code_objects(code)
    print(f"\n=== {pyc_path} ===")
    print(f"Total code objects: {len(all_codes)}")
    for name, co in all_codes:
        print(f"  {name} (argcount={co.co_argcount})")
