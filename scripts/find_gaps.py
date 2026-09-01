import sys, os, json
from pathlib import Path

PROJECT_ROOT = Path(r'F:\Downloads\pythoncdc-main')
index_file = PROJECT_ROOT / 'pyc_index.json'
with open(index_file, 'r', encoding='utf-8') as f:
    entries = json.load(f)

gaps = []
for entry in entries:
    if entry.get('decompile_status') == 'partial':
        total = entry.get('total_functions', 0)
        matched = entry.get('matched_functions', 0)
        gap = total - matched
        if gap >= 3:
            name = os.path.basename(entry.get('path', ''))
            gaps.append((gap, total, matched, name))

gaps.sort(reverse=True)
for gap, total, matched, name in gaps[:20]:
    print('%3d gaps (%3d/%3d): %s' % (gap, matched, total, name))
