# -*- coding: utf-8 -*-
"""Merge candidate specs into one spec PER core file, ordered by position, with chained proof.

  python -X utf8 mkfinal.py <out-prefix> <spec.json> [<spec.json> ...]

For each file touched: edits are sorted by their offset in the landed bytes, then replayed one by
one asserting the anchor still occurs EXACTLY ONCE after the previous edits were applied (so two
candidates that overlap the same hunk are caught here rather than at build time).
Writes <out-prefix>_<basename-of-file>.json next to this script and prints the net line counts.
"""
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/opencode/r65gate'
sys.stdout.reconfigure(encoding='utf-8')

prefix = sys.argv[1]
specs = sys.argv[2:]
byfile = {}
for sp in specs:
    s = json.load(io.open(sp, encoding='utf-8'))
    edits = s.get('edits') or [{'anchor': s['anchor'], 'repl': s['repl']}]
    byfile.setdefault(s['file'], []).extend([(os.path.basename(sp), e) for e in edits])

for rel, pairs in byfile.items():
    src = io.open(os.path.join(REPO, rel.replace('/', os.sep)), 'rb').read().decode('utf-8-sig').replace('\r\n', '\n')
    ordered = sorted(range(len(pairs)), key=lambda i: src.find(pairs[i][1]['anchor']))
    ordered = [pairs[i] for i in ordered]
    for i, (origin, e) in enumerate(ordered):
        assert src.find(e['anchor']) >= 0, 'anchor of %s edit %d not found' % (origin, i)
    merged = []
    cur = src
    for origin, e in ordered:
        n = cur.count(e['anchor'])
        assert n == 1, 'after previous edits, %s edit anchor occurs %d times (overlap?)' % (origin, n)
        cur = cur.replace(e['anchor'], e['repl'])
        merged.append(e)
    ins = sum(e['repl'].count('\n') - e['anchor'].count('\n') for e in merged)
    out = '%s/%s_%s.json' % (ROOT, prefix, os.path.basename(rel))
    io.open(out, 'w', encoding='utf-8').write(json.dumps(
        {'file': rel, 'edits': merged, 'sources': [o for o, _ in ordered]},
        ensure_ascii=False, indent=1))
    print('%-34s edits=%d lines=%+d  ->  %s' % (rel, len(merged), ins, os.path.basename(out)))
    print('    sources: %s' % ', '.join(o for o, _ in ordered))
