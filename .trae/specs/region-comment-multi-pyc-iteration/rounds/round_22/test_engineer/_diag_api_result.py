"""R22: check api_base while-else else_stmts generation"""
import sys
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc
import json

with open(r'f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
    index = json.load(f)

pyc_path = None
for e in index:
    if 'api_base.pyc' in e.get('path', ''):
        pyc_path = e['path']
        break

src = decompile_pyc(pyc_path)
lines = src.split('\n')
in_func = False
for i, line in enumerate(lines):
    if 'def decorate_api_exc' in line:
        in_func = True
    if in_func:
        print(f'{i+1:4d}: {line}')
        if line and not line[0].isspace() and i > 0 and 'def decorate_api_exc' not in line:
            break
