"""R22: diagnose 0% match pyc files"""
import json, os, sys
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

INDEX_PATH = r'f:/Downloads/pythoncdc-main/pyc_index.json'
with open(INDEX_PATH, 'r', encoding='utf-8') as f:
    index = json.load(f)

# Find 0% match entries
zeros = [(i, e) for i, e in enumerate(index)
         if e.get('decompile_status') == 'partial'
         and e.get('bytecode_match_rate', 0) == 0.0
         and e.get('function_count', 0) > 0]

print(f'Zero-match pyc files with functions: {len(zeros)}')

from pycdc import decompile_pyc

for idx, entry in zeros[:5]:
    pyc_path = entry['path']
    name = os.path.basename(pyc_path)
    if not os.path.exists(pyc_path):
        print(f'  SKIP: {name}')
        continue

    # Check if OK.py was generated
    ok_path = pyc_path.replace('.pyc', 'OK.py')
    has_ok = os.path.exists(ok_path)

    # Try to decompile
    try:
        dec_src = decompile_pyc(pyc_path)
        can_compile = True
        try:
            compile(dec_src, '<dec>', 'exec')
        except SyntaxError as se:
            can_compile = False
            compile_err = str(se)[:80]

        src_len = len(dec_src)
        status = 'OK' if can_compile else f'SYNTAX_ERR: {compile_err}'
        print(f'  {name}: OK.py={has_ok} src={src_len}B {status}')
    except Exception as e:
        print(f'  {name}: DECOMPILE_ERR: {str(e)[:80]}')
