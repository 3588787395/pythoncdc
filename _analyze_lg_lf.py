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

# Collect all LOAD_GLOBAL -> LOAD_FAST mismatches with context
lg_lf_patterns = {}
for missing, rate, path in worst[:50]:
    short = path.replace('F:/Downloads/pythoncdc-main/', '')
    result = subprocess.run([sys.executable, 'scripts/pyc_batch_verify.py', 'single', short],
                          capture_output=True, timeout=30, encoding='utf-8', errors='replace')
    for line in result.stdout.split('\n'):
        if 'first_diff' in line and 'orig_op' in line:
            orig_op_m = re.search(r"orig_op': '(\w+)'", line)
            decomp_op_m = re.search(r"decomp_op': '(\w+)'", line)
            orig_arg_m = re.search(r"orig_arg': ([^,}]+)", line)
            decomp_arg_m = re.search(r"decomp_arg': ([^,}]+)", line)
            if orig_op_m and decomp_op_m:
                orig_op = orig_op_m.group(1)
                decomp_op = decomp_op_m.group(1)
                if orig_op == 'LOAD_GLOBAL' and decomp_op == 'LOAD_FAST':
                    orig_arg = orig_arg_m.group(1).strip("'\"") if orig_arg_m else '?'
                    decomp_arg = decomp_arg_m.group(1).strip("'\"") if decomp_arg_m else '?'
                    key = f"{orig_arg} -> {decomp_arg}"
                    if key not in lg_lf_patterns:
                        lg_lf_patterns[key] = 0
                    lg_lf_patterns[key] += 1

# Also check for functions that have the mismatch  
func_mismatches = {}
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
        if in_mismatches and 'first_diff' in line and 'orig_op' in line:
            orig_op_m = re.search(r"orig_op': '(\w+)'", line)
            decomp_op_m = re.search(r"decomp_op': '(\w+)'", line)
            if orig_op_m and decomp_op_m:
                orig_op = orig_op_m.group(1)
                decomp_op = decomp_op_m.group(1)
                if orig_op == 'LOAD_GLOBAL' and decomp_op == 'LOAD_FAST':
                    if current_func not in func_mismatches:
                        func_mismatches[current_func] = 0
                    func_mismatches[current_func] += 1

print("LOAD_GLOBAL -> LOAD_FAST arg patterns:")
for k, v in sorted(lg_lf_patterns.items(), key=lambda x: -x[1]):
    print(f"  {v:3d}x {k}")

print(f"\nFunctions with LOAD_GLOBAL->LOAD_FAST mismatch count:")
for k, v in sorted(func_mismatches.items(), key=lambda x: -x[1])[:15]:
    print(f"  {v:3d}x {k}")
