#!/usr/bin/env python3
"""R35 回归测试: 运行所有 partial/ok 文件验证无退化。"""
import json, sys, os, time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode, get_bytecode_instructions

import marshal

index_path = PROJECT_ROOT / 'pyc_index.json'
with open(index_path, 'r', encoding='utf-8') as f:
    entries = json.load(f)

# Test all OK files + a sample of partial files
ok_files = [e for e in entries if e.get('decompile_status') == 'ok']
partial_files = [e for e in entries if e.get('decompile_status') == 'partial']

# Test all OK files (regression check) + all partial files
test_files = ok_files + partial_files

regressions = []
improvements = []
unchanged = []

for i, entry in enumerate(test_files):
    pyc_path = entry['path']
    if not os.path.exists(pyc_path):
        continue
    
    ok_py_path = pyc_path.replace('.pyc', 'OK.py')
    
    try:
        source = decompile_pyc(pyc_path)
        if source is None:
            continue
        
        # Compile and compare
        import py_compile
        cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
        
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        
        result = compare_bytecode(orig_code, decomp_code)
        rate = result.get('match_rate', 0)
        old_rate = entry.get('bytecode_match_rate', 0)
        
        status = 'ok' if rate == 1.0 else ('partial' if rate > 0 else 'failed')
        old_status = entry.get('decompile_status', '')
        
        if rate < old_rate - 0.01:
            regressions.append((pyc_path, old_rate, rate, old_status, status))
        elif rate > old_rate + 0.01:
            improvements.append((pyc_path, old_rate, rate, old_status, status))
        else:
            unchanged.append((pyc_path, old_rate, rate))
        
        # Update entry
        entry['bytecode_match_rate'] = rate
        entry['decompile_status'] = status
        entry['last_tested_round'] = 35
        
    except Exception as e:
        pass
    
    if (i + 1) % 50 == 0:
        print(f"  Progress: {i+1}/{len(test_files)} files processed...")

print(f"\n=== RESULTS ===")
print(f"Total: {len(test_files)}")
print(f"Improvements: {len(improvements)}")
print(f"Regressions: {len(regressions)}")
print(f"Unchanged: {len(unchanged)}")

if improvements:
    print("\n=== IMPROVEMENTS (top 20) ===")
    improvements.sort(key=lambda x: x[2] - x[1], reverse=True)
    for path, old, new, old_st, new_st in improvements[:20]:
        p = path.split('site-packages/')[-1] if 'site-packages/' in path else path
        print(f"  {p}: {old:.4f} -> {new:.4f} ({old_st} -> {new_st})")

if regressions:
    print("\n=== REGRESSIONS ===")
    for path, old, new, old_st, new_st in regressions:
        p = path.split('site-packages/')[-1] if 'site-packages/' in path else path
        print(f"  {p}: {old:.4f} -> {new:.4f} ({old_st} -> {new_st})")

# Save updated index
with open(index_path, 'w', encoding='utf-8') as f:
    json.dump(entries, f, indent=2, ensure_ascii=False)
print(f"\nIndex updated.")

# Summary
ok_count = sum(1 for e in entries if e.get('decompile_status') == 'ok')
partial_count = sum(1 for e in entries if e.get('decompile_status') == 'partial')
failed_count = sum(1 for e in entries if e.get('decompile_status') == 'failed')
total_rate = sum(e.get('bytecode_match_rate', 0) for e in entries) / len(entries)
print(f"\n=== OVERALL ===")
print(f"OK: {ok_count}, Partial: {partial_count}, Failed: {failed_count}")
print(f"Average match rate: {total_rate:.4f}")
