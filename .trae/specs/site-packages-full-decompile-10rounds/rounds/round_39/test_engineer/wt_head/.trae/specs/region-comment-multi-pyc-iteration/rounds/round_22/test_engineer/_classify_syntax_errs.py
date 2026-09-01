"""R22: classify syntax errors in batch results"""
import sys, os, json
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

with open(r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_22/batch_results.json', 'r') as f:
    results = json.load(f)

syntax_errs = [r for r in results['results'] if r.get('status') == 'syntax_error']
categories = {}
for r in syntax_errs:
    name = os.path.basename(r['path'])
    try:
        src = decompile_pyc(r['path'])
        compile(src, '<dec>', 'exec')
        cat = 'now_ok'
    except SyntaxError as se:
        cat = se.msg
    
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(name)

for cat, files in sorted(categories.items(), key=lambda x: -len(x[1])):
    print(f'{cat}: {len(files)} files')
    for f in files[:3]:
        print(f'  {f}')
