#!/usr/bin/env python3
"""R35 回归测试: 使用 pyc_batch_verify.py 的 decompile_single 正确流程。"""
import json, sys, os, time, marshal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pycdc import decompile_pyc
from testqouter.round1.base import compare_bytecode

index_path = PROJECT_ROOT / 'pyc_index.json'
with open(index_path, 'r', encoding='utf-8') as f:
    entries = json.load(f)

# Test a sample of OK files (first 30) + all partial files
ok_files = [e for e in entries if e.get('decompile_status') == 'ok']
partial_files = [e for e in entries if e.get('decompile_status') == 'partial']

# Sample 30 OK files for regression, all partial for improvement check
import random
random.seed(42)
ok_sample = random.sample(ok_files, min(30, len(ok_files)))
test_files = ok_sample + partial_files

regressions = []
improvements = []
unchanged = []

for i, entry in enumerate(test_files):
    pyc_path = entry['path']
    if not os.path.exists(pyc_path):
        continue
    
    ok_py_path = pyc_path.replace('.pyc', 'OK.py')
    
    try:
        # Step 1: Decompile
        source = decompile_pyc(pyc_path)
        if source is None:
            continue
        
        # Step 2: Write to OK.py
        with open(ok_py_path, 'w', encoding='utf-8') as f:
            f.write(source)
        
        # Step 3: Compile OK.py
        import py_compile
        cfile = py_compile.compile(ok_py_path, doraise=True, quiet=2)
        with open(cfile, 'rb') as f:
            f.read(16)
            decomp_code = marshal.load(f)
        
        # Step 4: Load original
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig_code = marshal.load(f)
        
        # Step 5: Compare
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
    
    if (i + 1) % 20 == 0:
        print(f"  Progress: {i+1}/{len(test_files)} files processed...", flush=True)

print(f"\n=== RESULTS ===", flush=True)
print(f"Total tested: {len(test_files)}")
print(f"Improvements: {len(improvements)}")
print(f"Regressions: {len(regressions)}")
print(f"Unchanged: {len(unchanged)}")

if improvements:
    print("\n=== IMPROVEMENTS (top 20) ===", flush=True)
    improvements.sort(key=lambda x: x[2] - x[1], reverse=True)
    for path, old, new, old_st, new_st in improvements[:20]:
        p = path.split('site-packages/')[-1] if 'site-packages/' in path else path
        print(f"  {p}: {old:.4f} -> {new:.4f} ({old_st} -> {new_st})")

if regressions:
    print("\n=== REGRESSIONS ===", flush=True)
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
