#!/usr/bin/env python3
"""R101: Find set_universe in OK.py"""
import sys, os, json
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')

with open('f:/Downloads/pythoncdc-main/pyc_index.json', 'r', encoding='utf-8') as f:
    pyc_index = json.load(f)

for entry in pyc_index:
    if os.path.basename(entry['path']) != 'api_base.pyc':
        continue
    ok_path = entry['path'].replace('.pyc', 'OK.py')
    if not os.path.exists(ok_path):
        continue
    with open(ok_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    in_func = False
    for i, line in enumerate(lines, 1):
        if 'def set_universe' in line:
            in_func = True
        if in_func:
            print(f"  {i:4d}: {line.rstrip()[:80]}")
            if i > 0 and in_func and line.strip() == '':
                # Check if next line is another def/class
                if i < len(lines) and (lines[i].startswith('def ') or lines[i].startswith('class ') or lines[i].startswith('    def ')):
                    break
    break
