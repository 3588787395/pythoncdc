import json, subprocess, sys, re

with open('pyc_index.json') as f:
    idx = json.load(f)

pattern_counts = {}
total_mismatches = 0
processed = 0

for p in idx:
    if p.get('decompile_status') != 'partial':
        continue
    path = p['path']
    processed += 1
    try:
        r = subprocess.run([sys.executable, 'scripts/pyc_batch_verify.py', 'single', path], 
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    except:
        continue
    
    in_mismatches = False
    for line in r.stdout.split('\n'):
        line = line.strip()
        if 'mismatches' in line and '(' in line:
            in_mismatches = True
            continue
        if in_mismatches and line.startswith('- '):
            total_mismatches += 1
        if in_mismatches and 'first_diff' in line:
            m = re.search(r"orig_op': '([^']+)'.*decomp_op': '([^']+)'", line)
            if m:
                key = f'{m.group(1)} -> {m.group(2)}'
                pattern_counts[key] = pattern_counts.get(key, 0) + 1
            else:
                m2 = re.search(r"'orig_op': '([^']+)'.*'decomp_op': '([^']+)'", line)
                if m2:
                    key = f'{m2.group(1)} -> {m2.group(2)}'
                    pattern_counts[key] = pattern_counts.get(key, 0) + 1
        if in_mismatches and not line.startswith('-') and not line.startswith('first_diff') and not line.startswith('{') and line:
            in_mismatches = False

print(f'Processed: {processed} partial files, Total mismatches: {total_mismatches}')
print(f'Top patterns by first_diff orig_op -> decomp_op:')
for k, v in sorted(pattern_counts.items(), key=lambda x: -x[1])[:25]:
    print(f'  {v:3d}x {k}')
