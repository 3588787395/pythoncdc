# Dump full R5 diff details for REAL46-046 (and 022/023 if quick).
import json, os, sys, subprocess
ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, os.path.join(ROOT, 'tools', 'completeness'))
import semantic_diff as sd

space = json.load(open(os.path.join(ROOT, r'.trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json'), encoding='utf-8'))
entries = {e['id']: e for e in space['entries'] if isinstance(e, dict)}

eid = sys.argv[1] if len(sys.argv) > 1 else 'REAL46-046'
entry = entries[eid]
pyc = os.path.join(ROOT, entry['pyc'])
product_dir = r'D:\temp\opencode\g2c_r5_products'
os.makedirs(product_dir, exist_ok=True)
product = os.path.join(product_dir, eid + '.py')

# decompile with current tree
r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'pycdc.py'), pyc, '-o', product],
                   capture_output=True, text=True, timeout=120)
print('decompile rc', r.returncode, (r.stderr or '')[-200:])

case = {
    'case_id': eid,
    'original': {'pyc': pyc},
    'product': {'source': product},
    'entrypoint': 'module',
    'args': [], 'kwargs': {}, 'timeout_s': 60,
    '_base': ROOT,
}
calls = (entry.get('input_model') or {}).get('calls')
if calls:
    case['call_exprs'] = [str(c) for c in calls if str(c).strip()]

result = sd.compare_case(case)
print('status', result.get('status'))
print()
for d in result.get('diffs', []):
    if isinstance(d, dict) and d.get('dimension') != 'R7':
        print('-'*50)
        print(json.dumps(d, ensure_ascii=False, indent=1)[:1500])
print()
print('errors:', result.get('errors', [])[:5])
print('inconclusive:', result.get('inconclusive', [])[:5])
