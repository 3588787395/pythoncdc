import subprocess, sys, os, re

pyc_dir = r'F:\Downloads\pythoncdc-main\site-packages'

proc = subprocess.Popen(
    [sys.executable, r'F:\Downloads\pythoncdc-main\scripts\pyc_batch_verify.py', 'batch'],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True, encoding='utf-8', errors='replace'
)
output, _ = proc.communicate(timeout=600)

partial_pycs = []
current = None
for line in output.split('\n'):
    if '.pyc' in line and 'PARTIAL' not in line:
        for part in line.strip().split():
            if part.endswith('.pyc') and os.path.exists(part):
                current = part
                break
    if 'PARTIAL' in line and current:
        partial_pycs.append(current)
        current = None

for pyc_file in partial_pycs:
    proc = subprocess.Popen(
        [sys.executable, r'F:\Downloads\pythoncdc-main\scripts\pyc_batch_verify.py', 'single', pyc_file],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace'
    )
    output, _ = proc.communicate(timeout=120)
    
    # Find mismatch details
    for line in output.split('\n'):
        line = line.strip()
        if 'mismatches' in line or 'match_rate' in line or 'matched_functions' in line:
            print(f"{os.path.basename(pyc_file)}: {line}")
