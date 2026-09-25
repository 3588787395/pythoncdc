# -*- coding: utf-8 -*-
"""diag2 R66 probe #4: state of the chain-head prefix-assign owner at call time.

Pure pass-through wrapper (ORIG is invoked first, unchanged, and its result is
returned verbatim); afterwards it only RECORDS into a list that is written to
disk once decompilation finished, so nothing can perturb generation.

For every _generate_chain_head_prefix_assign call it logs:
  head   : chain-head block (start, #ins, last op)
  owner  : the expression region whose merge_block IS that head block
           (class, merge_context, cond/merge block, generated-blocks mask,
            membership in _generated_regions / _generating_regions)
  out    : returned statement AST types + which ones are Assign + short label
  stack  : emitting frames

usage: python -X utf8 probe_disc.py --out=logs/disc.txt <pyc> [<pyc> ...]
"""
import argparse
import io
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.dont_write_bytecode = True
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

ap = argparse.ArgumentParser()
ap.add_argument('pycs', nargs='+')
ap.add_argument('--out', default='logs/disc.txt')
a = ap.parse_args()

import pycdc  # noqa
import core.cfg.region_ast_generator as G  # noqa
from core.cfg.region_ast_generator import (  # noqa
    BoolOpRegion, TernaryRegion)

ORIG = G.RegionASTGenerator._generate_chain_head_prefix_assign
REC = []
CUR = ['']


def bd(b):
    try:
        return '%d(%dins,%s)' % (b.start, len(b.instructions),
                                 b.instructions[-1].opname)
    except Exception:
        return '?'


def label(s):
    if not isinstance(s, dict):
        return type(s).__name__
    t = s.get('type')
    if t == 'Assign':
        tg = (s.get('targets') or [None])[0]
        return 'Assign:%s' % (tg.get('id') if isinstance(tg, dict) else tg)
    if t == 'Expr':
        v = s.get('value') or {}
        f = v.get('func') if isinstance(v, dict) else None
        if isinstance(f, dict):
            return 'Expr:%s.%s' % (f.get('value', {}).get('id', '?')
                                   if isinstance(f.get('value'), dict) else '?',
                                   f.get('attr') or f.get('id'))
        return 'Expr:%s' % (v.get('type') if isinstance(v, dict) else '?')
    return t


def snap(self, head_block):
    owners = []
    if head_block is None:
        return owners
    for _rr in self.regions:
        if (isinstance(_rr, (BoolOpRegion, TernaryRegion))
                and getattr(_rr, 'merge_block', None) is head_block):
            blk = getattr(_rr, 'blocks', None) or []
            owners.append({
                'cls': type(_rr).__name__,
                'ctx': getattr(_rr, 'merge_context', None),
                'cond': bd(getattr(_rr, 'condition_block', None)),
                'nblk': len(blk),
                'allblk_gen': bool(blk) and all(
                    b in self.generated_blocks for b in blk),
                'mask': ''.join('G' if b in self.generated_blocks
                                else '-' for b in blk),
                'gen_id': id(_rr) in getattr(self, '_generated_regions', set()),
                'ing_id': id(_rr) in getattr(self, '_generating_regions', set()),
                'hkey': id(head_block) in getattr(self, '_chain_head_active', set()),
            })
    return owners


def wrapper(self, head_block, *args, **kw):
    try:
        pre = snap(self, head_block)
    except Exception as e:
        pre = [{'rec-error': repr(e)}]
    r = ORIG(self, head_block, *args, **kw)
    try:
        ent = {'file': CUR[0], 'head': bd(head_block), 'pre': pre,
               'owners': snap(self, head_block)}
        ent['out'] = [label(s) for s in (r if isinstance(r, list) else ([r] if r else []))]
        REC.append(ent)
    except Exception as e:  # recording must never alter generation
        REC.append({'file': CUR[0], 'rec-error': repr(e)})
    return r


G.RegionASTGenerator._generate_chain_head_prefix_assign = wrapper

for p in a.pycs:
    CUR[0] = p.replace('\\', '/').rsplit('/', 1)[-1]
    try:
        pycdc.decompile_pyc(p)
    except Exception as e:
        REC.append({'file': CUR[0], 'run-error': repr(e)[:200]})

ROW = ('        %-3s %-13s ctx=%-9s cond=%-12s mask=%-6s allblk_gen=%-5s '
       'gen_id=%-5s ing_id=%-5s hkey=%s\n')


def fmt(tag, o):
    return ROW % (tag, o.get('cls', '?'), o.get('ctx'), o.get('cond'),
                  o.get('mask'), o.get('allblk_gen'), o.get('gen_id'),
                  o.get('ing_id'), o.get('hkey'))


with io.open(a.out, 'w', encoding='utf-8') as fh:
    fh.write('chain-head prefix-assign calls recorded: %d\n\n' % len(REC))
    for e in REC:
        fh.write('%-28s head=%-18s out=%s\n'
                 % (e['file'], e.get('head'), e.get('out')))
        for o in (e.get('pre') or []):
            fh.write(fmt('PRE', o))
        for o in (e.get('owners') or []):
            fh.write(fmt('POST', o))
        if 'rec-error' in e:
            fh.write('        ERROR %s\n' % e['rec-error'])
print(io.open(a.out, encoding='utf-8').read()[:14000])
