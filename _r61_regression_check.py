#!/usr/bin/env python3
"""R61: Quick regression check - test previously OK files to find regressions"""
import json
import subprocess
import sys
import os
from pathlib import Path

os.chdir("f:/Downloads/pythoncdc-main")
os.environ['PYTHONIOENCODING'] = 'utf-8'

index_path = Path("pyc_index.json")
with open(index_path, 'r', encoding='utf-8') as f:
    index = json.load(f)

# Get files that were previously OK with 100% match rate
ok_files = [e for e in index if e["decompile_status"] == "ok" and e["bytecode_match_rate"] == 1.0]
print(f"Total previously OK files: {len(ok_files)}")
sys.stdout.flush()

# Test each one quickly
regressions = []
still_ok = 0
for i, entry in enumerate(ok_files):
    pyc_path = entry["path"]
    rel_path = pyc_path.replace("F:/Downloads/pythoncdc-main/", "").replace("F:\\Downloads\\pythoncdc-main\\", "")
    rel_path = rel_path.replace("/", os.sep)
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/pyc_batch_verify.py", "single", rel_path],
            capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace'
        )
        output = (result.stdout or "") + (result.stderr or "")
    except Exception as e:
        print(f"  ERROR [{i+1}]: {rel_path}: {e}")
        sys.stdout.flush()
        continue
    
    # Parse match rate
    is_ok = "decompile_status:   ok" in output and "match_rate:        100.00%" in output
    
    if not is_ok:
        # Extract rate
        rate = "?"
        for line in output.split('\n'):
            if 'match_rate:' in line:
                rate = line.split(':')[1].strip()
        regressions.append((rel_path, rate))
        print(f"  REGRESSION [{i+1}/{len(ok_files)}]: {rel_path} rate={rate}")
        sys.stdout.flush()
    else:
        still_ok += 1
    
    if (i + 1) % 20 == 0:
        print(f"  Progress: {i+1}/{len(ok_files)} checked, {still_ok} OK, {len(regressions)} regressions")
        sys.stdout.flush()

print(f"\n=== SUMMARY ===")
print(f"Total checked: {len(ok_files)}")
print(f"Still OK: {still_ok}")
print(f"Regressions: {len(regressions)}")
for path, rate in regressions:
    print(f"  - {path}: {rate}%")
sys.stdout.flush()
