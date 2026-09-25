# -*- coding: utf-8 -*-
"""diag2 R66 probe: duplicate owner ledger for load_bars_from_hundsun.

Counts, per (head_block, owner region) pair, how many times
_generate_chain_head_prefix_assign re-runs _generate_ternary and whether the
region had already been generated / its blocks marked generated at that moment.
"""
import io
import json
import os
import sys
import traceback

REPO = r'F:\Downloads\pythoncdc-main'
sys.dont_write_bytecode = True
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')
import pycdc  # noqa
import core.cfg.region_ast_generator as G  # noqa

MARK = sys.argv[1] if len(sys.argv) > 1 else 'load_bars_from_hundsun'
OUT = r'D:/Temp/opencode/r66gate/diag2/logs/chp_ledger.txt'
log = []
ORIG = G.RegionASTGenerator._generate_chain_head_prefix_assign


def bd(b):
    return None if b is None else '%d(%dins,%s)' % (
        b.start, len(b.instructions), b.instructions[-1].opname)


def w(self, head_block, *a, **k):
    fr = traceback.extract_stack()[:-1]
    keep = [f for f in fr if 'region_ast_generator' in f.filename]
    ent = {'head': bd(head_block), 'nblk_head': len(head_block.instructions)
           if head_block is not None else 0,
           'stack': ' <- '.join('%s:%d' % (f.name, f.lineno) for f in keep[-6:])}
    r = ORIG(self, head_block, *a, **k)
    # which owner region did it pick? redo the lookup for reporting
    owner = None
    if head_block is not None:
        for _rr in self.regions:
            if getattr(_rr, 'merge_block', None) is head_block and \
                    type(_rr).__name__ in ('BoolOpRegion', 'TernaryRegion'):
                owner = _rr
                break
    ent['owner'] = None if owner is None else {
        'cls': type(owner).__name__,
        'ctx': getattr(owner, 'merge_context', None),
        'vt': str(getattr(owner, 'value_target', None)),
        'cond': bd(getattr(owner, 'condition_block', None)),
        'gen_region': id(owner) in getattr(self, '_generated_regions', set()),
        'blk_gen': [bd(b) + ('|GEN' if b in self.generated_blocks else '|-')
                    for b in (getattr(owner, 'blocks', None) or [])],
    }
    ent['out_types'] = [s.get('type') for s in (r or [])]
    ent['out_has_marker'] = MARK in repr(r)
    log.append(ent)
    return r


G.RegionASTGenerator._generate_chain_head_prefix_assign = w
text = pycdc.decompile_pyc(sys.argv[2] if len(sys.argv) > 2 else
                           REPO + '/site-packages/fly/data/quote.pyc')
with io.open(OUT, 'w', encoding='utf-8') as fh:
    for i, e in enumerate(log):
        if e['out_has_marker'] or (e['owner'] or {}).get('ctx') == 'fstring':
            fh.write('[%d] %s\n' % (i, json.dumps(e, ensure_ascii=False, indent=1)))
    fh.write('\ntotal chain_head calls=%d ; marker-emitting=%d ; fstring-owner=%d\n'
             % (len(log), sum(1 for e in log if e['out_has_marker']),
                sum(1 for e in log if (e['owner'] or {}).get('ctx') == 'fstring')))
    fh.write('\nproduct marker lines:\n')
    for n, line in enumerate(text.split('\n'), 1):
        if MARK in line and 'def ' not in line:
            fh.write('%d| %s\n' % (n, line[:120]))
print(io.open(OUT, encoding='utf-8').read())
