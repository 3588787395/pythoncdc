"""[fixA] 权威口径（pyc_verify.py/pylingual compare_pyc）34 小测试集读数 vs failing_index.json 基线 Movement Matrix。"""
import json

BASE = r'.trae/specs/adversarial-complete-forms-v2-10rounds/baseline/failing_index.json'
AFTER = r'.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_fixA/tmp/fixA_34set_pycverify.json'

base_rows = json.load(open(BASE, encoding='utf-8'))
after = json.load(open(AFTER, encoding='utf-8'))
bmap = {}
for r in base_rows:
    key = (r.get('pyc') or r.get('path')).replace('\\', '/')
    bmap[key] = r

b_s = b_t = a_s = a_t = 0
improve, regress, same_fail = [], [], []
for row in after['rows']:
    key = row['pyc'].replace('\\', '/')
    b = bmap.get(key)
    if b is None:
        print('NO BASELINE:', key)
        continue
    b_s += b['units_success']; b_t += b['units_total']
    a_s += row['units_success']; a_t += row['units_total']
    name = key.split('site-packages/')[-1]
    if row['units_success'] > b['units_success']:
        improve.append((name, b['units_success'], b['units_total'], row['units_success'], row['units_total']))
    elif row['units_success'] < b['units_success']:
        regress.append((name, b['units_success'], b['units_total'], row['units_success'], row['units_total'], row['failures']))
    elif row['failures']:
        same_fail.append((name, row['units_success'], row['units_total'], len(row['failures'])))

print('TOTAL baseline=%d/%d  after=%d/%d' % (b_s, b_t, a_s, a_t))
print('IMPROVED (%d):' % len(improve))
for r in improve:
    print('  + %s %d/%d -> %d/%d' % r)
print('REGRESSED (%d):' % len(regress))
for r in regress:
    print('  - %s %d/%d -> %d/%d' % r[:5])
    for f in r[5][:4]:
        print('      ', f.replace('***', ''))
print('SAME-FAILURE FILES (%d):' % len(same_fail))
for r in same_fail:
    print('  = %s %d/%d (%d fail)' % r)
