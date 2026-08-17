#!/usr/bin/env python3
"""Batch verification of all ok pyc files"""
import sys, marshal, dis, ast, subprocess, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

ok_count = 0
fail_count = 0
fail_list = []

for entry in index:
    pyc_path = entry['path']
    status = entry.get('decompile_status', 'unknown')
    if status != 'ok':
        continue
    try:
        result = subprocess.run(
            [sys.executable, 'pycdc.py', pyc_path, '-o', pyc_path.replace('.pyc', 'OK.py')],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            fail_count += 1
            fail_list.append(f'{pyc_path}: decompile failed')
            continue
        
        py_path = pyc_path.replace('.pyc', 'OK.py')
        if not Path(py_path).exists():
            fail_count += 1
            fail_list.append(f'{pyc_path}: no output')
            continue
        
        source = Path(py_path).read_text(encoding='utf-8')
        try:
            decomp_code = compile(source, py_path, 'exec')
        except SyntaxError as e:
            fail_count += 1
            fail_list.append(f'{pyc_path}: syntax error: {e}')
            continue
        
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.loads(f.read())
        
        orig_instrs = list(dis.get_instructions(orig_code))
        decomp_instrs = list(dis.get_instructions(decomp_code))
        
        if len(orig_instrs) == len(decomp_instrs):
            match = True
            for o, d in zip(orig_instrs, decomp_instrs):
                if o.opname != d.opname:
                    match = False
                    break
            if match:
                ok_count += 1
            else:
                fail_count += 1
                fail_list.append(f'{pyc_path}: opcode mismatch')
        else:
            fail_count += 1
            fail_list.append(f'{pyc_path}: instr count {len(orig_instrs)} vs {len(decomp_instrs)}')
    except Exception as e:
        fail_count += 1
        fail_list.append(f'{pyc_path}: {e}')

print(f'OK: {ok_count}, FAIL: {fail_count}')
for f in fail_list[:20]:
    print(f'  {f}')
