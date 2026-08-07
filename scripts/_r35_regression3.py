#!/usr/bin/env python3
"""R35 回归测试: 用 pyc_batch_verify.decompile_single 正确测试。"""
import json, sys, os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Use the proper decompile_single from pyc_batch_verify
from scripts.pyc_batch_verify import decompile_single

index_path = PROJECT_ROOT / 'pyc_index.json'
with open(index_path, 'r', encoding='utf-8') as f:
    entries = json.load(f)

ok_files = [e for e in entries if e.get('decompile_status') == 'ok']
partial_files = [e for e in entries if e.get('decompile_status') == 'partial']

# Sample 20 OK files for regression, all partial for improvement check
import random
random.seed(42)
ok_sample = random.sample(ok_files, min(20, len(ok_files)))
test_files = ok_sample + partial_files

regressions = []
improvements = []
unchanged = []
errors = []

for i, entry in enumerate(test_files):
    pyc_path = entry['path']
    if not os.path.exists(pyc_path):
        continue
    
    ok_py_path = pyc_path.replace('.pyc', 'OK.py')
    old_rate = entry.get('bytecode_match_rate', 0)
    old_status = entry.get('decompile_status', '')
    
    try:
        result = decompile_single(pyc_path, ok_py_path)
        rate = result.get('match_rate', 0)
        status = result.get('decompile_status', 'failed')
        
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
        errors.append((pyc_path, str(e)[:100]))
    
    if (i + 1) % 20 == 0:
        print(f"  Progress: {i+1}/{len(test_files)} files processed...", flush=True)

print(f"\n=== RESULTS ===", flush=True)
print(f"Total tested: {len(test_files)}")
print(f"Improvements: {len(improvements)}")
print(f"Regressions: {len(regressions)}")
print(f"Unchanged: {len(unchanged)}")
print(f"Errors: {len(errors)}")

if improvements:
    print("\n=== IMPROVEMENTS (top 20) ===", flush=True)
    improvements.sort(key=lambda x: x[2] - x[1], reverse=True)
    for path, old, new, old_st, new_st in improvements[:20]:
        p = path.split('site-packages/')[-1] if 'site-packages/' in path else path
        print(f"  {p}: {old:.4f} -> {new:.4f} ({old_st} -> {new_st})")

if regressions:
    print("\n=== REGRESSIONS (top 20) ===", flush=True)
    for path, old, new, old_st, new_st in regressions[:20]:
        p = path.split('site-packages/')[-1] if 'site-packages/' in path else path
        print(f"  {p}: {old:.4f} -> {new:.4f} ({old_st} -> {new_st})")

if errors:
    print("\n=== ERRORS (first 5) ===", flush=True)
    for path, err in errors[:5]:
        p = path.split('site-packages/')[-1] if 'site-packages/' in path else path
        print(f"  {p}: {err}")

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
