"""R22: find and diagnose a syntax-error pyc"""
import json, os, sys
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

INDEX = r'f:/Downloads/pythoncdc-main/pyc_index.json'
with open(INDEX, 'r', encoding='utf-8') as f:
    index = json.load(f)

partial = [(i, e) for i, e in enumerate(index)
           if e.get('decompile_status') == 'partial']

for idx, entry in partial:
    pyc_path = entry['path']
    if not os.path.exists(pyc_path):
        continue
    try:
        dec_src = decompile_pyc(pyc_path)
        try:
            compile(dec_src, '<dec>', 'exec')
        except SyntaxError as se:
            name = os.path.basename(pyc_path)
            print(f'{name}: SyntaxError at line {se.lineno}: {se.msg}')
            lines = dec_src.split('\n')
            for i in range(max(0, se.lineno - 3), min(len(lines), se.lineno + 2)):
                marker = '>>>' if i + 1 == se.lineno else '   '
                print(f'{marker} {i+1:4d}: {lines[i][:100]}')
            print()
    except Exception:
        pass
