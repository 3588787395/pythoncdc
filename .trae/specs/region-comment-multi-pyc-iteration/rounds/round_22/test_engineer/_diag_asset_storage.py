"""R22: diagnose asset_storage.pyc syntax error"""
import sys
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc
import json

with open(r'f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
    index = json.load(f)

pyc_path = None
for e in index:
    if 'asset_storage.pyc' in e.get('path', ''):
        pyc_path = e['path']
        break

src = decompile_pyc(pyc_path)
lines = src.split('\n')

# Find the syntax error
try:
    compile(src, '<dec>', 'exec')
except SyntaxError as se:
    for i in range(max(0, se.lineno-10), min(len(lines), se.lineno+3)):
        marker = '>>>' if i+1 == se.lineno else '   '
        print(f'{marker} {i+1:4d}: {lines[i]}')
