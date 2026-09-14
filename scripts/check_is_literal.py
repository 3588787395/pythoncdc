#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '.')
from pycdc import decompile_pyc
import json

with open('pyc_index.json') as f:
    entries = json.load(f)

partials = [e for e in entries if e.get('decompile_status') == 'partial']

is_literal_count = 0
is_literal_files = []

for entry in partials:
    pyc_path = entry['path']
    if not os.path.exists(pyc_path):
        continue
    try:
        src = decompile_pyc(pyc_path)
        has_is_literal = False
        for line in src.split('\n'):
            stripped = line.strip()
            tokens = stripped.split()
            for i, t in enumerate(tokens):
                if t == 'is' and i > 0 and i < len(tokens) - 1:
                    next_t = tokens[i+1].rstrip(',)')
                    try:
                        int(next_t)
                        has_is_literal = True
                        break
                    except ValueError:
                        pass
                    if next_t.startswith('"') or next_t.startswith("'"):
                        has_is_literal = True
                        break
            if has_is_literal:
                break
        if has_is_literal:
            is_literal_count += 1
            is_literal_files.append(os.path.basename(pyc_path))
    except:
        pass

print(f'Files with IS_LITERAL pattern (x is <literal>): {is_literal_count}')
for f in is_literal_files:
    print(f'  {f}')
