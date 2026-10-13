# -*- coding: utf-8 -*-
"""block_walk.py -- for every traced walk frame, per block: lines executed, emission reached?

usage: python -X utf8 block_walk.py
Reads logs/lines_r110.json + logs/census_r110_traced.json written by walk_census_r110.py.
"""
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace',
                              line_buffering=True)
M = 'D:/Temp/r110/'
GEN = open(M + 'core/cfg/region_ast_generator.py', encoding='utf-8-sig',
           errors='replace').read().replace('\r\n', '\n').split('\n')
import os
CEN = os.environ.get('CEN', 'logs/census_r110_traced.json')
LIN = os.environ.get('LIN', 'logs/lines_r110.json')
OUT = os.environ.get('BOUT', 'logs/block_walk.json')
TARGETS = set(json.load(open(M + CEN))['targets'])
frames = json.load(open(M + LIN))
calls = json.load(open(M + CEN))['calls']

# consumed-by-emission: _generate_block_statements calls whose parent stack has frame seq
emitted = {}   # (frame_seq, block_off) -> True
for c in calls:
    if c['meth'] == '_generate_block_statements':
        blk = c['info'].get('blk')
        for st in c['parent_stack']:
            for s in st:
                emitted[(s, blk)] = True


def src(n):
    try:
        return GEN[n - 1].strip()[:96]
    except Exception:
        return '?'


PINNED = {'_process_if_blocks': 26765, '_generate_try_body': 29936,
          '_loop_generate_body': 8763}
SECONDARY = {'_process_if_blocks': 28174}


def loop_line(log, fn):
    """pinned main body-sequence 'for' line of this walk (cross-checked vs frequency)"""
    from collections import Counter
    if fn in PINNED:
        return PINNED[fn]
    c = Counter(ln for ln, b in log if b is not None)
    return c.most_common(1)[0][0] if c else None


print('=== %d traced walk frames ===' % len(frames))
out = []
for f in sorted(frames, key=lambda x: x['seq']):
    log = f['log']
    ll = loop_line(log, f['fn'])
    # group consecutive runs by block value
    groups = []
    cur = None
    for ln, b in log:
        if ln == ll:
            if cur:
                groups.append(cur)
            cur = {'blk': b, 'lines': [ln]}
            continue
        if cur is None:
            cur = {'blk': b, 'lines': []}
        cur['lines'].append(ln)
    if cur:
        groups.append(cur)
    pre = []
    if groups and groups[0]['blk'] is None:
        pre = groups.pop(0)['lines']
    seen_blocks = [g['blk'] for g in groups if g['blk'] is not None]
    print('\n--- seq=%-5d %-24s reg=%-20s nblk_arg=%-5s loop_line=%s blocks_iterated=%d lines=%d'
          % (f['seq'], f['fn'], f['reg'], f['nblk_arg'], ll, len(seen_blocks), len(log)))
    print('    loop header source: %s' % src(ll))
    rows = []
    for g in groups:
        b = g['blk']
        if b is None:
            continue
        lines = g['lines']
        comp = []
        for ln in lines:
            if comp and comp[-1][0] == ln:
                comp[-1][1] += 1
            else:
                comp.append([ln, 1])
        last = lines[-1] if lines else None
        emit = (f['seq'], b) in emitted
        istgt = b in TARGETS
        rows.append((b, istgt, emit, len(lines), last,
                     ' '.join('%d%s' % (ln, ('x%d' % k) if k > 1 else '')
                              for ln, k in comp)))
    for b, istgt, emit, nl, last, comp in rows:
        if istgt or True:
            tag = 'TARGET' if istgt else '      '
            print('    @%-6s %s emitted=%-5s nlines=%-3d last=%-6s | %s'
                  % (b, tag, emit, nl, last, comp[:400]))
    out.append({'seq': f['seq'], 'fn': f['fn'], 'reg': f['reg'], 'loop_line': ll, 'secondary': SECONDARY.get(f['fn']),
                'iterated': seen_blocks,
                'rows': [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]})
json.dump(out, open(M + OUT, 'w'))
