import sys, os, json, subprocess
sys.path.insert(0, '.')
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

d = json.load(open('pyc_index.json'))
partials = [p for p in d if p.get('decompile_status') == 'partial']

from collections import Counter
patterns = Counter()
func_patterns = Counter()

for p in partials:
    path = p['path']
    result = subprocess.run(
        [sys.executable, 'scripts/pyc_batch_verify.py', 'single', path],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        timeout=30
    )
    output = result.stdout + result.stderr
    for line in output.split('\n'):
        if 'first_diff' in line:
            import re
            m = re.search(r"orig_op[=:]['\"](\w+)['\"], (?:decomp_op|orig_arg)[=:]['\"]?(\w*)['\"]?", line)
            if m:
                key = f"{m.group(1)} -> {m.group(2)}"
                patterns[key] += 1
            m2 = re.search(r"orig_op[=:]['\"](\w+)['\"], decomp_op[=:]['\"](\w+)['\"]", line)
            if m2:
                key2 = f"{m2.group(1)} -> {m2.group(2)}"
                func_patterns[key2] += 1

print("Top first_diff orig_op -> decomp_op patterns:")
for pattern, count in func_patterns.most_common(25):
    print(f"  {count:4d} {pattern}")
