import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
d = json.load(open(r'.trae/specs/attain-true-completeness/rounds/round4/rec1_probes_r4pre1b.json', encoding='utf-8'))
if isinstance(d, dict):
    d = d.get('probes', [])
for p in d:
    print(json.dumps(p, ensure_ascii=False)[:260])
