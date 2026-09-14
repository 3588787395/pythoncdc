import subprocess, json, re, sys

with open(r'F:\Downloads\pythoncdc-main\pyc_index.json') as f:
    data = json.load(f)

partials = [e for e in data if e.get('decompile_status') == 'partial']
first_diffs = {}

for entry in partials:
    path = entry.get('path', '')
    result = subprocess.run(
        ['python', r'F:\Downloads\pythoncdc-main\scripts\pyc_batch_verify.py', 'single', path],
        capture_output=True, text=True, timeout=120, encoding='utf-8', errors='replace')
    for line in result.stdout.split('\n'):
        if 'first_diff:' in line:
            m = re.search(r"orig_op[=:]['\"]?(\w+)", line)
            d = re.search(r"decomp_op[=:]['\"]?(\w+)", line)
            if m and d:
                key = (m.group(1), d.group(1))
            else:
                key = line.strip()[:80]
            name = path.split('site-packages/')[-1]
            if key not in first_diffs:
                first_diffs[key] = []
            first_diffs[key].append(name)
            break

for key, files in sorted(first_diffs.items(), key=lambda x: -len(x[1])):
    print('%-40s %d files: %s' % (str(key), len(files), ', '.join(files[:5])))
