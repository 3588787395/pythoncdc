# -*- coding: utf-8 -*-
"""census_table.py -- render the walk census JSON as the offset x walk table.

usage: python -X utf8 census_table.py [logs/census_r110.json]
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace',
                              line_buffering=True)
path = sys.argv[1] if len(sys.argv) > 1 else 'D:/Temp/r110/logs/census_r110.json'
d = json.load(open(path))
TARGETS = d['targets']
calls = d['calls']

print('stats:', json.dumps(d['stats'], ensure_ascii=False))
print()
print('=== every watched call that had >=1 target block in hand, in time order ===')
for c in sorted(calls, key=lambda x: x['seq']):
    keys = [k for k in c['info'] if k.endswith('blocks') or k.startswith('arg')]
    desc = []
    for k in keys:
        v = c['info'][k]
        if k == 'blk':
            desc.append('blk=%s' % v)
            continue
        idx = v.get('idx') or v.get('hits')
        n = v.get('n')
        if isinstance(idx, dict):
            pairs = sorted(idx.items(), key=lambda t: t[1])
            desc.append('%s n=%s idx=%s' % (k, n, pairs))
        else:
            desc.append('%s n=%s hits=%s' % (k, n, v.get('hits')))
    print('seq=%-5d %-28s reg=%-22s branch=%-8s depth=%d parent=%s' % (
        c['seq'], c['meth'], c['reg'], c.get('branch'), c['depth'],
        c['parent_stack'][0] if c['parent_stack'] else []))
    print('        targets=%s' % c['targets'])
    for s in desc:
        print('        %s' % s)
    print('        gb_before=%s' % c['gb_before'])
    print('        gb_after =%s  nret=%s events=%s' % (c.get('gb_after'), c.get('nret'),
                                                       c.get('events')))
    print()

print('=== per-offset: which lists contained it, in time order ===')
for t in TARGETS:
    rows = []
    for c in sorted(calls, key=lambda x: x['seq']):
        if t not in c['targets']:
            continue
        pos = []
        for k, v in c['info'].items():
            if k == 'blk':
                if v == t:
                    pos.append('AS-BLOCK')
                continue
            idx = v.get('idx') or {}
            if t in idx:
                pos.append('%s[%d]/%d' % (k, idx[t], v['n']))
            elif t in (v.get('hits') or []):
                pos.append('%s*' % k)
        rows.append('seq%d %s reg=%s br=%s pos=%s gb(b=%s,a=%s) nret=%s' % (
            c['seq'], c['meth'], c['reg'], c.get('branch'), ','.join(pos),
            c['gb_before'].get(str(t), c['gb_before'].get(t)),
            (c.get('gb_after') or {}).get(str(t), (c.get('gb_after') or {}).get(t)),
            c.get('nret')))
    print('@%-6d  n_lists=%d' % (t, len(rows)))
    for r in rows:
        print('        ' + r)
