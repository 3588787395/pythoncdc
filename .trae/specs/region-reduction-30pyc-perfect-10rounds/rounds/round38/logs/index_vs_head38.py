# -*- coding: utf-8 -*-
"""Round 38 (zero-change round) integrity proof: the shipped index must still be a *measurement*
of the landed bytes, not a self-report.

`g4_head.all.jsonl` was produced by the batch harness over all 402 corpus files with
--arm=head, where `head` is a private mirror of core/ asserted byte-equal to the worktree
(sha256[:20] 6b0759b1a0a566a4eb8f == commit 7b8af974's blob).  Here we replay every row against
pyc_index.json field by field and count conflicts, so "nothing moved this round" is measured
rather than assumed.

usage: python -X utf8 index_vs_head38.py <head.jsonl>
"""
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')

rows = [json.loads(l) for l in io.open(sys.argv[1], encoding='utf-8') if l.strip()]
assert len(rows) == 402, len(rows)
idx = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
assert len(idx) == 402

by_path = {}
for r in rows:
    key = r.get('path') or r.get('pyc')
    by_path[os.path.abspath(key).replace('\\', '/').lower()] = r

out, conflicts, err = [], [], 0
for e in idx:
    p = e['path'].replace('\\', '/')
    full = os.path.abspath(os.path.join(REPO, 'site-packages', p)).replace('\\', '/').lower() \
        if not p.startswith('F:') else p.lower()
    r = by_path.get(full)
    if r is None:
        cand = [v for k, v in by_path.items() if k.endswith(p.lower())]
        assert len(cand) == 1, ('unresolved', p, len(cand))
        r = cand[0]
    if r.get('error'):
        err += 1
        conflicts.append((p, 'harness-error', r['error']))
        continue
    for a, b in (('function_count', 'total_functions'), ('matched_functions', 'matched_functions')):
        if e[a] != r[b]:
            conflicts.append((p, a, '%s(index) vs %s(measured)' % (e[a], r[b])))

print('rows 402  harness-errors %d  index-vs-measured conflicts %d' % (err, len(conflicts)))
for c in conflicts[:40]:
    print('  CONFLICT', c)
sf, sm = sum(e['function_count'] for e in idx), sum(e['matched_functions'] for e in idx)
mf, mm = sum(r['total_functions'] for r in rows), sum(r['matched_functions'] for r in rows)
print('index   Σtotal %d Σmatched %d  fully-matched files %d' % (sf, sm, sum(
    1 for e in idx if e['matched_functions'] == e['function_count'])))
print('measured Σtotal %d Σmatched %d  fully-matched files %d' % (mf, mm, sum(
    1 for r in rows if r['total_functions'] and r['matched_functions'] == r['total_functions'])))
