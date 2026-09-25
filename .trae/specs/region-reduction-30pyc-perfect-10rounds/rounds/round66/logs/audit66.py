# -*- coding: utf-8 -*-
"""Audit a 402-arm dump against the committed pyc_index.json entries."""
import io
import json
import os
import sys

REPO = r'F:/Downloads/pythoncdc-main'
dump_path = sys.argv[1]
recs = [json.loads(l) for l in io.open(dump_path, encoding='utf-8') if l.strip()]
idx = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
entries = idx['entries'] if isinstance(idx, dict) and 'entries' in idx else idx
by_path = {}
for e in entries:
    by_path[os.path.normpath(e['path']).replace('\\', '/')] = e

sp = (REPO + '/site-packages/').replace('/', os.sep)
miss = []
bad = []
m = 0
t = 0
seen = set()
for r in recs:
    p = os.path.normpath(r['path']).replace('\\', '/')
    seen.add(p)
    e = by_path.get(p)
    m += r['matched_functions']
    t += r['total_functions']
    if e is None:
        miss.append(p)
        continue
    if (e.get('matched_functions'), e.get('function_count'), e.get('decompile_status')) != \
       (r['matched_functions'], r['total_functions'], 'ok' if not r['mism'] else 'partial'):
        bad.append((p, (e.get('matched_functions'), e.get('function_count'), e.get('decompile_status')),
                    (r['matched_functions'], r['total_functions'], 'ok' if not r['mism'] else 'partial')))
notseen = [p for p in by_path if p not in seen]
print('records=%d matched=%d total=%d clean_files=%d' % (
    len(recs), m, t, sum(1 for r in recs if not r['mism'])))
print('errors=%d' % sum(1 for r in recs if r.get('error')))
print('index entries not in dump=%d dump paths not in index=%d' % (len(notseen), len(miss)))
print('per-entry mismatches=%d' % len(bad))
for b in bad[:12]:
    print('  ', b[0].split('site-packages/')[-1], 'index=', b[1], 'measured=', b[2])
