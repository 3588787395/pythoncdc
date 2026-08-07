"""R22: diagnose jq_trans_module syntax error"""
import os, sys
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

PYC = r'f:/Downloads/pythoncdc-main/site-packages/fly/data/jq_trans_module.pyc'
if not os.path.exists(PYC):
    # Try other paths
    import json
    with open(r'f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
        index = json.load(f)
    for e in index:
        if 'jq_trans_module' in e.get('path', ''):
            PYC = e['path']
            break

print(f'Path: {PYC}')
dec_src = decompile_pyc(PYC)

# Find the syntax error context
try:
    compile(dec_src, '<dec>', 'exec')
    print('Compile: OK')
except SyntaxError as se:
    lines = dec_src.split('\n')
    start = max(0, se.lineno - 10)
    end = min(len(lines), se.lineno + 5)
    print(f'SyntaxError at line {se.lineno}: {se.msg}')
    for i in range(start, end):
        marker = '>>>' if i + 1 == se.lineno else '   '
        print(f'{marker} {i+1:4d}: {lines[i]}')
