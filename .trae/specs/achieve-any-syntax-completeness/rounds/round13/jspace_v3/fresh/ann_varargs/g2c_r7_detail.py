# Print R7 diff samples for an entry (REAL46-031 default).
import json, os, sys, subprocess
ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, os.path.join(ROOT, 'tools', 'completeness'))
import semantic_diff as sd

space = json.load(open(os.path.join(ROOT, r'.trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json'), encoding='utf-8'))
entries = {e['id']: e for e in space['entries'] if isinstance(e, dict)}

eid = sys.argv[1] if len(sys.argv) > 1 else 'REAL46-031'
entry = entries[eid]
pyc = os.path.join(ROOT, entry['pyc'])
product_dir = r'D:\temp\opencode\g2c_r5_products'
os.makedirs(product_dir, exist_ok=True)
product = os.path.join(product_dir, eid + '.py')

r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'pycdc.py'), pyc, '-o', product],
                   capture_output=True, text=True, timeout=180)
print('decompile rc', r.returncode)

case = {
    'case_id': eid,
    'original': {'pyc': pyc},
    'product': {'source': product},
    'entrypoint': 'module',
    'args': [], 'kwargs': {}, 'timeout_s': 120,
    '_base': ROOT,
}
calls = (entry.get('input_model') or {}).get('calls')
if calls:
    case['call_exprs'] = [str(c) for c in calls if str(c).strip()]

result = sd.compare_case(case)
print('status', result.get('status'))
diffs = [d for d in result.get('diffs', []) if isinstance(d, dict)]
r7 = [d for d in diffs if d.get('dimension') == 'R7']
print('total diffs', len(diffs), 'R7', len(r7))
from collections import Counter
paths = Counter()
for d in r7:
    p = d.get('path', '')
    # group by the metadata field name
    key = p.split('.')[2] if p.startswith('$.metadata.code.') and len(p.split('.')) > 2 else p
    paths[key] += 1
print('R7 field histogram:', dict(paths))
print()
for d in r7[:12]:
    print('-'*40)
    print(json.dumps(d, ensure_ascii=False)[:600])
