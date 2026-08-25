import json, subprocess, sys, os, re

with open('pyc_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count files by how close they are to 100%
near_full = []
for entry in data:
    rate = entry.get('bytecode_match_rate', 0)
    total = entry.get('function_count', 0)
    matched = round(total * rate)
    missing = total - matched
    if missing > 0 and missing <= 3 and total > 1:
        near_full.append((missing, rate, total, entry['path']))

near_full.sort()
print(f"Files with 1-3 missing functions (closest to 100%): {len(near_full)}")
total_missing_near = sum(x[0] for x in near_full)
print(f"Total missing in these files: {total_missing_near}")
print()
for missing, rate, total, path in near_full[:30]:
    short = path.replace('F:/Downloads/pythoncdc-main/', '')
    print(f"  -{missing} ({rate:.0%}, {round(total*rate)}/{total}) {short}")
