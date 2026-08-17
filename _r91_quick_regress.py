#!/usr/bin/env python3
"""R91 quick regression test on key pyc files"""
import sys, os, json
sys.path.insert(0, '.')
from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

# Load the index
with open('pyc_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

# Test first 10 files from the index
tested = 0
matched = 0
for entry in index[:20]:
    pyc_path = entry.get('path', '')
    if not os.path.exists(pyc_path):
        continue
    try:
        decomp_src = decompile_pyc(pyc_path)
        decomp_code = compile(decomp_src, '<decompiled>', 'exec')
        result = compare_bytecode(pyc_path, decomp_src)
        is_match = result.get('match', False)
        td = len(result.get('true_diffs', []))
        jd = len(result.get('jump_diffs', []))
        status = "OK" if is_match else "FAIL"
        print(f"  {status:4s} td={td:4d} jd={jd:4d} - {pyc_path}")
        tested += 1
        if is_match:
            matched += 1
    except Exception as e:
        print(f"  ERR  {str(e)[:60]} - {pyc_path}")
        tested += 1

print(f"\nQuick regression: {matched}/{tested} matched")
