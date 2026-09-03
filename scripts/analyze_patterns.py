import json, subprocess, sys, re

with open('pyc_index.json', 'r') as f:
    data = json.load(f)

partials = [e for e in data if e.get('decompile_status') == 'partial']
patterns = {}

for p in partials:
    pyc_path = p['path']
    rel = pyc_path.split('site-packages/')[-1]
    result = subprocess.run(
        [sys.executable, 'scripts/pyc_batch_verify.py', 'single', pyc_path],
        capture_output=True, text=True, encoding='utf-8', timeout=120
    )
    output = result.stdout
    for line in output.split('\n'):
        if 'first_diff' in line:
            orig_m = re.search(r"orig_op': '(\w+)'", line)
            decomp_m = re.search(r"decomp_op': '(\w+)'", line)
            if orig_m and decomp_m:
                key = (orig_m.group(1), decomp_m.group(1))
                patterns.setdefault(key, []).append(rel)
            elif 'missing_in_decomp' in line:
                patterns.setdefault(('MISSING', ''), []).append(rel)
            break

print('First diff patterns across %d partial files:' % len(partials))
for k, v in sorted(patterns.items(), key=lambda x: -len(x[1])):
    print('  %2d files: orig=%-25s decomp=%s' % (len(v), k[0], k[1]))
    for f in v[:3]:
        print('             %s' % f)
