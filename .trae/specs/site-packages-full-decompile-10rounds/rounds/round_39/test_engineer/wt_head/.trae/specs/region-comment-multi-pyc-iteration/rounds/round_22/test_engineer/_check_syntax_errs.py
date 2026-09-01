"""R22: check syntax errors after while-else fix"""
import json, sys, os
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

with open(r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_22/batch_results.json', 'r') as f:
    results = json.load(f)

syntax_errs = [r for r in results['results'] if r.get('status') == 'syntax_error']
print(f'Syntax error files: {len(syntax_errs)}')
for r in syntax_errs[:10]:
    name = os.path.basename(r['path'])
    try:
        src = decompile_pyc(r['path'])
        compile(src, '<dec>', 'exec')
        print(f'  {name}: compile OK now')
    except SyntaxError as se:
        print(f'  {name}: SyntaxError line {se.lineno}: {se.msg}')
        lines = src.split('\n')
        for i in range(max(0, se.lineno-2), min(len(lines), se.lineno+1)):
            marker = '>>>' if i+1 == se.lineno else '   '
            print(f'    {marker} {i+1:4d}: {lines[i][:80]}')
