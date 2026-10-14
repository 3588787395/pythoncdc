# -*- coding: utf-8 -*-
"""block_walk2.py -- CORRECT per-block attribution: each non-header line event is attributed to
the block value live in f_locals at that instant (no off-by-one grouping).

usage: python -X utf8 block_walk2.py <lines.json> <census.json>
"""
import io
import json
import sys
from collections import OrderedDict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace',
                              line_buffering=True)
M = 'D:/Temp/r110/'
GEN = open(M + 'core/cfg/region_ast_generator.py', encoding='utf-8-sig',
           errors='replace').read().replace('\r\n', '\n').split('\n')
LIN, CEN = sys.argv[1], sys.argv[2]
cen = json.load(open(M + CEN))
TARGETS = set(cen['targets'])
frames = json.load(open(M + LIN))
LOOP = {'_process_if_blocks': 26765, '_generate_try_body': 29936,
        '_loop_generate_body': 8763}
GUARD = {'_process_if_blocks': 26775, '_generate_try_body': 29937,
         '_loop_generate_body': 8764}
CONT = {'_process_if_blocks': 26776, '_generate_try_body': 29938,
        '_loop_generate_body': 8765}
HOT = {26869: 'nested region dispatch _generate_region(_nr)',
       26911: 'CLAIM self.generated_blocks.add(_nb) over _nr.blocks',
       26930: 'CLAIM add(_lb) over _lr.blocks',
       8941: '_loop_dispatch_block(...)',
       8947: 'body_blocks_no_header.append(block) (defer to postprocess)',
       30069: '_generate_region(_r08_loop_child)',
       30068: 'r08 discard(b)',
       30076: 'CLAIM add(b) over _r08_loop_child.blocks',
       28174: 'successor-absorption loop',
       28287: 'final claim of the walk'}


def src(n):
    try:
        return (GEN[n - 1].strip() if n else '?')[:84]
    except Exception:
        return '?'


for f in sorted(frames, key=lambda x: x['seq']):
    fn = f['fn']
    hl = LOOP.get(fn)
    per = OrderedDict()
    for ln, b in f['log']:
        if ln == hl or b is None:
            continue
        per.setdefault(b, []).append(ln)
    tg = [b for b in per if b in TARGETS]
    if not tg and hl is None:
        continue
    print('\n=== seq=%-5s %-24s reg=%-22s nblk_arg=%-5s blocks_seen=%d targets_seen=%d'
          % (f['seq'], fn, f['reg'], f['nblk_arg'], len(per), len(tg)))
    if hl:
        print('    walk header %s: %s' % (hl, src(hl)))
        print('    membership guard %s: %s -> continue %s' % (GUARD[fn], src(GUARD[fn]),
                                                              src(CONT[fn])))
    for b in tg:
        ls = per[b]
        g = GUARD.get(fn)
        skipped = (g in ls) and (CONT.get(fn) in ls) and not any(
            x in HOT and x != g for x in ls)
        hot = [x for x in sorted(set(ls)) if x in HOT]
        print('    @%-6s lines=%-4d %-28s hot=%s' % (
            b, len(ls), 'SKIPPED-BY-GUARD' if skipped else 'walked',
            [(h, HOT[h]) for h in hot]))
