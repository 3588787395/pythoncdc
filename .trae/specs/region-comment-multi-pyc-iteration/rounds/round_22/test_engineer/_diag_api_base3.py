"""R22: show api_base decompiled code around error"""
import sys, json, os
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

with open(r'f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
    index = json.load(f)

pyc_path = None
for e in index:
    if 'api_base.pyc' in e.get('path', ''):
        pyc_path = e['path']
        break

dec_src = decompile_pyc(pyc_path)
lines = dec_src.split('\n')

# Show lines 25-35
for i in range(24, min(36, len(lines))):
    print(f'{i+1:4d}: {lines[i]}')
