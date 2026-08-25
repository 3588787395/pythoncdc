import json, subprocess, sys, os, re

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

worst = []
for entry in data:
    rate = entry.get('bytecode_match_rate', 0)
    total = entry.get('function_count', 0)
    matched = round(total * rate)
    missing = total - matched
    if missing > 0:
        worst.append((missing, rate, entry['path']))
worst.sort(reverse=True)

# Find SWAP mismatches
for missing, rate, path in worst[:50]:
    short = path.replace('F:/Downloads/pythoncdc-main/', '')
    result = subprocess.run([sys.executable, 'scripts/pyc_batch_verify.py', 'single', short],
                          capture_output=True, timeout=30, encoding='utf-8', errors='replace')
    in_mismatches = False
    current_func = None
    for line in result.stdout.split('\n'):
        m = re.match(r'\s+- (\w+):', line)
        if m:
            current_func = m.group(1)
            in_mismatches = True
        if in_mismatches and 'first_diff' in line and "'SWAP'" in line:
            print(f"SWAP mismatch in {short} function {current_func}")
            print(f"  {line.strip()}")
