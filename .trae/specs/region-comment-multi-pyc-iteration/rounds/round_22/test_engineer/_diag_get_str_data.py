"""R22: diagnose quotation.pyc get_str_data truncation"""
import os, sys
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

OK_PY = r'f:/Downloads/pythoncdc-main/site-packages/fly/data/quotationOK.py'

with open(OK_PY, 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_func = False
func_lines = []
indent = 0
for i, line in enumerate(lines):
    if 'def get_str_data' in line:
        in_func = True
        indent = len(line) - len(line.lstrip())
        func_lines.append(f'{i+1}: {line.rstrip()}')
        continue
    if in_func:
        cur_indent = len(line) - len(line.lstrip())
        if line.strip() and cur_indent <= indent and not line.strip().startswith('#'):
            break
        func_lines.append(f'{i+1}: {line.rstrip()}')

print(f'get_str_data ({len(func_lines)} lines):')
for line in func_lines[:60]:
    print(line)
if len(func_lines) > 60:
    print(f'... ({len(func_lines) - 60} more lines)')
    for line in func_lines[-10:]:
        print(line)
