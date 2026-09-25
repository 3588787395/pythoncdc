# -*- coding: utf-8 -*-
"""G5: per-entry audit of the index written back by this round's `batch --all`.

  python -X utf8 audit5_g5.py

Reads HEAD's `pyc_index.json` (`git show`, read-only) and the working-tree index, then reports
  * entries added / removed,
  * entries whose ONLY change is the round stamp,
  * every other entry change field by field,
plus the aggregate status/matched deltas. The expectation for a clean round is: nothing removed,
nothing added, and the substantive change set == the files the candidate set actually touched.
"""
import io
import json
import subprocess
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')

raw = subprocess.run(['git', 'show', 'HEAD:pyc_index.json'], cwd=REPO,
                     capture_output=True, text=True, encoding='utf-8').stdout
assert raw.strip(), 'git show failed'
old = json.loads(raw)
new = json.loads(io.open(REPO + r'\pyc_index.json', encoding='utf-8').read())


def as_dict(ix):
    ents = ix['entries'] if isinstance(ix, dict) and 'entries' in ix else ix
    if isinstance(ents, dict):
        return dict(ents)
    return dict((e['path'], e) for e in ents)


o, n = as_dict(old), as_dict(new)
print('entries HEAD=%d worktree=%d' % (len(o), len(n)))
added = sorted(set(n) - set(o))
removed = sorted(set(o) - set(n))
print('added=%d removed=%d' % (len(added), len(removed)))
for p in added[:10]:
    print('   + %s' % p)
for p in removed[:10]:
    print('   - %s' % p)

ROUND_KEYS = {'last_tested_round', 'round'}
stamp_only = 0
substantive = []
keyshape = 0
for p in sorted(set(o) & set(n)):
    a, b = o[p], n[p]
    if set(a) != set(b):
        keyshape += 1
        print('   KEYDIFF %s  +%s -%s' % (p, sorted(set(b) - set(a)), sorted(set(a) - set(b))))
    diffs = [(k, a[k], b[k]) for k in sorted(set(a) & set(b)) if a[k] != b[k]]
    if not diffs:
        continue
    if all(k in ROUND_KEYS for k, _, _ in diffs):
        stamp_only += 1
        continue
    substantive.append((p, diffs))
print('key-shape diffs=%d  round-stamp-only=%d  substantive=%d' % (keyshape, stamp_only, len(substantive)))
for p, diffs in substantive:
    print('   %s' % p.split('site-packages/')[-1])
    for k, x, y in diffs:
        print('        %-22s %r -> %r' % (k, x, y))


def totals(ix):
    vs = list(ix.values())
    f = lambda e, k, d=0: (e.get(k) if isinstance(e, dict) else None)
    st = {}
    for e in vs:
        st[e.get('decompile_status')] = st.get(e.get('decompile_status'), 0) + 1
    return st, sum(e.get('matched_functions') or 0 for e in vs), sum(e.get('function_count') or 0 for e in vs)


so, mo, fo = totals(o)
sn, mn, fn = totals(n)
print('status HEAD=%s' % so)
print('status NEW =%s' % sn)
print('matched HEAD=%d/%d  NEW=%d/%d  delta=%+d' % (mo, fo, mn, fn, mn - mo))
