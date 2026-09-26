# -*- coding: utf-8 -*-
import json
import io
import re
import collections

rep = json.load(io.open(r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round70/logs/gate/G3v_pycverify_r70.json', encoding='utf-8'))
rows = rep['rows']
ix = {}
for e in json.load(io.open(r'F:/Downloads/pythoncdc-main/pyc_index.json', encoding='utf-8')):
    ix[e['path'].replace(chr(92), '/')] = e
cat_re = re.compile(r'(Missing bytecode|Extra bytecode|Different control flow|Different bytecode)')
stat = collections.Counter()
filecat = []
for r in rows:
    if r['status'] == 'success':
        continue
    cats = collections.Counter()
    for f in r.get('failures', []):
        m = cat_re.search(f)
        c = m.group(1) if m else 'other'
        cats[c] += 1
    top = ','.join('%s:%d' % kv for kv in cats.most_common())
    e = ix.get(r['pyc'].replace(chr(92), '/'), {})
    filecat.append({
        'file': r['pyc'].split('site-packages/')[-1],
        'pyc': r['pyc'].replace(chr(92), '/'),
        'official_status': e.get('decompile_status'),
        'official': '%s/%s' % (e.get('matched_functions'), e.get('total_functions')),
        'pylingual': '%d/%d' % (r['units_success'], r['units_total']),
        'cats': dict(cats),
        'top': top,
        'cf': cats.get('Different control flow', 0),
        'failures': [f[:200] for f in r.get('failures', [])[:40]],
    })
    for c in cats:
        stat[c] += cats[c]
print('failure files:', len(filecat))
print('category totals across failing units:', dict(stat))
print()
print('--- officially OK but pylingual failure (divergence set, highest priority) ---')
div = [x for x in filecat if x['official_status'] == 'ok']
for x in sorted(div, key=lambda t: -t['cf']):
    print('%-58s off=%s pyl=%s cf=%-3d %s' % (x['file'], x['official'], x['pylingual'], x['cf'], x['top']))
print('divergence count:', len(div))
print()
print('--- partial files (expected failures) sorted by control-flow units ---')
for x in sorted([x for x in filecat if x['official_status'] != 'ok'], key=lambda t: -t['cf'])[:12]:
    print('%-58s off=%s/%s pyl=%s cf=%-3d %s' % (x['file'], x['official_status'], x['official'], x['pylingual'], x['cf'], x['top']))
io.open(r'D:/Temp/opencode/r71gate/filecat.json', 'w', encoding='utf-8').write(json.dumps(filecat, ensure_ascii=False, indent=1))
print('written D:/Temp/opencode/r71gate/filecat.json')
