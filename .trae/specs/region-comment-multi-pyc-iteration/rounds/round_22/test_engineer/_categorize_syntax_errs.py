"""R22: categorize syntax errors in partial pyc"""
import json, os, sys
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

INDEX_PATH = r'f:/Downloads/pythoncdc-main/pyc_index.json'
with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    index = json.load(f)

from pycdc import decompile_pyc

partial = [(i, e) for i, e in enumerate(index)
           if e.get('decompile_status') == 'partial']

syntax_errs = {}
total_partial = 0
total_tested = 0

for idx, entry in partial:
    pyc_path = entry['path']
    if not os.path.exists(pyc_path):
        continue
    total_partial += 1

    try:
        dec_src = decompile_pyc(pyc_path)
        try:
            compile(dec_src, '<dec>', 'exec')
        except SyntaxError as se:
            total_tested += 1
            err_msg = str(se)
            # Categorize
            if 'expected an indented block after' in err_msg:
                keyword = err_msg.split("after '")[1].split("'")[0] if "after '" in err_msg else 'unknown'
                cat = f'empty_block_after_{keyword}'
            elif 'invalid syntax' in err_msg:
                cat = 'invalid_syntax'
            elif 'unmatched' in err_msg.lower():
                cat = 'unmatched_paren'
            else:
                cat = 'other'
            syntax_errs[cat] = syntax_errs.get(cat, 0) + 1
    except Exception:
        pass

print(f'Partial pyc files: {total_partial}')
print(f'With syntax errors: {total_tested}')
print(f'\nSyntax error categories:')
for cat, count in sorted(syntax_errs.items(), key=lambda x: -x[1]):
    print(f'  {cat}: {count}')
