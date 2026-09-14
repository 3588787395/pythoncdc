import json
import subprocess
import sys
import re
from collections import Counter

data = json.load(open('pyc_index.json'))
partial_files = [item['path'] for item in data if item.get('decompile_status') == 'partial']

print("Processing {} partial files...".format(len(partial_files)))

pair_counter = Counter()
file_errors = []
results_detail = []

for i, fpath in enumerate(partial_files):
    try:
        result = subprocess.run(
            [sys.executable, 'scripts/pyc_batch_verify.py', 'single', fpath],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=60,
            cwd=r'F:\Downloads\pythoncdc-main'
        )
        output = result.stdout + result.stderr

        # Parse first_diff lines like:
        # first_diff: {'index': 162, 'orig_op': 'JUMP_BACKWARD', 'decomp_op': 'PUSH_EXC_INFO', 'orig_arg': 86, 'decomp_arg': None}
        for line in output.split('\n'):
            line = line.strip()
            if 'first_diff' in line and 'orig_op' in line:
                # Extract the dict portion
                match = re.search(r"first_diff:\s*(\{.*\})", line)
                if match:
                    try:
                        d = json.loads(match.group(1).replace("'", '"'))
                        orig_op = d.get('orig_op')
                        decomp_op = d.get('decomp_op')
                        if orig_op and decomp_op:
                            pair_counter[(orig_op, decomp_op)] += 1
                            # Also extract function name from preceding context
                            results_detail.append((fpath, orig_op, decomp_op))
                    except json.JSONDecodeError:
                        # Try ast.literal_eval for Python dicts with single quotes
                        import ast
                        try:
                            d = ast.literal_eval(match.group(1))
                            orig_op = d.get('orig_op')
                            decomp_op = d.get('decomp_op')
                            if orig_op and decomp_op:
                                pair_counter[(orig_op, decomp_op)] += 1
                                results_detail.append((fpath, orig_op, decomp_op))
                        except:
                            pass

        if (i+1) % 10 == 0:
            print("  Processed {}/{}".format(i+1, len(partial_files)))

    except Exception as e:
        file_errors.append((fpath, str(e)))

print("\nDone. {} errors.".format(len(file_errors)))
if file_errors:
    for fe in file_errors[:10]:
        print("  Error: {}: {}".format(fe[0], fe[1]))

print("\nTotal mismatch entries: {}".format(sum(pair_counter.values())))
print("Unique (orig_op, decomp_op) pairs: {}".format(len(pair_counter)))
print()
print("=" * 70)
hdr_orig = "orig_op"
hdr_decomp = "decomp_op"
hdr_count = "count"
print("{:<35} {:<35} {:>8}".format(hdr_orig, hdr_decomp, hdr_count))
print("=" * 70)
for (orig, decomp), count in pair_counter.most_common():
    print("{:<35} {:<35} {:>8}".format(orig, decomp, count))
