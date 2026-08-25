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

patterns = {}
for missing, rate, path in worst[:50]:
    short = path.replace('F:/Downloads/pythoncdc-main/', '')
    result = subprocess.run([sys.executable, 'scripts/pyc_batch_verify.py', 'single', short],
                          capture_output=True, timeout=30, encoding='utf-8', errors='replace')
    for line in result.stdout.split('\n'):
        if 'first_diff' in line and 'orig_op' in line:
            # Parse dict-like format
            orig_op_m = re.search(r"orig_op': '(\w+)'", line)
            decomp_op_m = re.search(r"decomp_op': '(\w+)'", line)
            orig_arg_m = re.search(r"orig_arg': ([^,}]+)", line)
            decomp_arg_m = re.search(r"decomp_arg': ([^,}]+)", line)
            if orig_op_m and decomp_op_m:
                orig_op = orig_op_m.group(1)
                decomp_op = decomp_op_m.group(1)
                orig_arg = orig_arg_m.group(1).strip("'\"")[:25] if orig_arg_m else '?'
                decomp_arg = decomp_arg_m.group(1).strip("'\"")[:25] if decomp_arg_m else '?'
                key = f"{orig_op} -> {decomp_op}"
                if key not in patterns:
                    patterns[key] = {'count': 0, 'examples': []}
                patterns[key]['count'] += 1
                if len(patterns[key]['examples']) < 3:
                    patterns[key]['examples'].append(f"{orig_arg} -> {decomp_arg}")

print("Top mismatch patterns across worst 20 files:")
for k, v in sorted(patterns.items(), key=lambda x: -x[1]['count']):
    ex = v['examples'][0] if v['examples'] else ''
    print(f"  {v['count']:3d}x {k}  (e.g. {ex})")
