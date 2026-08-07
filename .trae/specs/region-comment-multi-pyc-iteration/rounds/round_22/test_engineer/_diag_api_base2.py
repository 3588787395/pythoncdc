"""R22: diagnose api_base.pyc else-indent error in detail"""
import marshal, sys, types, json, os
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

with open(r'f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
    index = json.load(f)

pyc_path = None
for e in index:
    if 'api_base.pyc' in e.get('path', ''):
        pyc_path = e['path']
        break

# Find the function with error
dec_src = decompile_pyc(pyc_path)
lines = dec_src.split('\n')

# Find else: followed by same-indent statement
errors = []
for i in range(len(lines) - 1):
    stripped = lines[i].strip()
    if stripped.endswith('else:') or stripped.endswith('except:') or stripped.endswith('finally:'):
        if i + 1 < len(lines):
            kw_indent = len(lines[i]) - len(lines[i].lstrip())
            next_stripped = lines[i+1].strip()
            if next_stripped:
                next_indent = len(lines[i+1]) - len(lines[i+1].lstrip())
                if next_indent <= kw_indent:
                    errors.append((i+1, lines[i].strip(), next_stripped))

print(f'Found {len(errors)} indent errors:')
for lineno, kw_line, next_line in errors:
    print(f'  Line {lineno}: after "{kw_line}" got "{next_line[:60]}"')
    # Show context
    for j in range(max(0, lineno-4), min(len(lines), lineno+2)):
        marker = '>>>' if j+1 == lineno else '   '
        print(f'{marker} {j+1:4d}: {lines[j][:80]}')
    print()
