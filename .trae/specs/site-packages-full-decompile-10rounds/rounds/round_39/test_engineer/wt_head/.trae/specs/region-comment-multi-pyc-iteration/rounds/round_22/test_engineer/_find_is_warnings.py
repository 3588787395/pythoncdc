"""R23: find files with 'is' literal warnings"""
import sys, os, json, marshal, types, warnings
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

with open(r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_22/batch_results.json', 'r') as f:
    results = json.load(f)

partials = [r for r in results['results'] if r.get('status') == 'partial']

is_warning_files = set()
for r in partials[:30]:
    pyc_path = r['path']
    if not os.path.exists(pyc_path):
        continue
    try:
        src = decompile_pyc(pyc_path)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            compile(src, '<dec>', 'exec')
        for warning in w:
            if 'is' in str(warning.message) and 'literal' in str(warning.message):
                name = os.path.basename(pyc_path)
                if name not in is_warning_files:
                    is_warning_files.add(name)
                    # Find the line in source
                    lines = src.split('\n')
                    if warning.lineno and warning.lineno <= len(lines):
                        print(f'{name}: {warning.message} at line {warning.lineno}')
                        print(f'  {lines[warning.lineno-1][:80]}')
    except:
        pass

print(f'\nTotal files with "is" literal warnings: {len(is_warning_files)}')
