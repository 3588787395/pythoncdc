# -*- coding: utf-8 -*-
"""Round 34 line C, read-only: is there a same-level discriminant that keeps R34-E's gain on
`default_event_source :: events` but rejects the false positives that broke
`r4_06` / `r4_07`?

Wraps RegionAnalyzer._cleanup_try_else_in_loop_body, recomputes exactly what that method
computes (parent loops, parent_body, the landed `spurious` verdict, A2's entry-exclusivity
predicate) and adds the two exit-side facts under test:

  E1  _eb is an enclosing loop's back_edge_block / header_block   (continue-landing)
  E2  _eb's tail instruction is a *backward* jump whose target is some loop header other
      than the child's own                                             (continue-landing)

Then calls the original untouched. Writes nothing but stdout.

usage: python -X utf8 probe_else34.py <pyc> [<pyc> ...]
"""
import os
import sys

REPO = r'F:/Downloads/pythoncdc-main'
CORE = os.environ.get('PROBE_CORE', REPO)
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, CORE)
sys.path.append(REPO)

import pycdc  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402
import core.cfg.region_analyzer as RA  # noqa: E402

_got = os.path.dirname(os.path.abspath(pycdc.__file__)).replace('\\', '/')
assert _got == CORE.replace('\\', '/').rstrip('/'), 'probe resolved to %s not %s' % (_got, CORE)
FCJ = RA.FORWARD_CONDITIONAL_JUMP_OPS
ITER_OPS = ('FOR_ITER', 'GET_ANEXT')

_orig = RegionAnalyzer._cleanup_try_else_in_loop_body


def _b(block):
    return None if block is None else block.start_offset


def _excl(lr, eb, self):
    """A2's R34-E predicate, re-implemented for measurement only."""
    h = lr.header_block
    if h is None or eb is None:
        return False
    if {p.start_offset for p in eb.predecessors} != {h.start_offset}:
        return False
    t = h.get_last_instruction()
    if t is None or t.opname not in ITER_OPS:
        return False
    return t.argval is not None and self.cfg.get_block_by_offset(t.argval) is eb


def _wrap(self, loop_regions, try_regions):
    cfgname = getattr(self.cfg, 'name', '?')
    rows = []
    for lr in loop_regions:
        if not lr.else_blocks:
            continue
        parents = [pl for pl in loop_regions
                   if pl is not lr and hasattr(pl, 'body_blocks') and pl.body_blocks
                   and any(b in pl.body_blocks for b in lr.body_blocks)]
        if not parents:
            continue
        pbody = set()
        for pl in parents:
            pbody.update(pl.body_blocks)
        cond_exit = set()
        if lr.has_break and lr.condition_block and lr.condition_block != lr.header_block:
            cl = lr.condition_block.get_last_instruction()
            if cl and cl.opname in FCJ and cl.argval is not None:
                ce = self.cfg.get_block_by_offset(cl.argval)
                if ce and not self._check_block_has_trailing_return_none(ce):
                    cond_exit.add(ce)
        for eb in lr.else_blocks:
            landed_strips = (eb in pbody) and (eb not in cond_exit)
            t = eb.get_last_instruction()
            e1 = any(eb is getattr(pl, 'back_edge_block', None) for pl in parents)
            e1h = any(eb is pl.header_block for pl in parents)
            e2 = False
            if t is not None and t.opname.startswith('JUMP_BACKWARD') and t.argval is not None:
                tgt = self.cfg.get_block_by_offset(t.argval)
                e2 = tgt is not None and tgt is not lr.header_block and \
                    any(tgt is pl.header_block for pl in loop_regions)
            rows.append((cfgname, _b(lr.header_block), _b(eb),
                         sorted(_b(p) for p in eb.predecessors),
                         sorted(_b(s) for s in eb.successors),
                         '%s%s' % (t.opname if t else '-',
                                   '->' + str(t.argval) if t and t.argval is not None else ''),
                         landed_strips, _excl(lr, eb, self), e1, e1h, e2,
                         [(_b(pl.header_block), _b(getattr(pl, 'back_edge_block', None)))
                          for pl in parents]))
    rv = _orig(self, loop_regions, try_regions)
    if rows:
        print('=== cfg=%s' % cfgname)
        print('  lr.hdr  eb   preds        succs      term                     landed_strip '
              'r34e_excl  E1_backedge  E1_parenthdr  E2_backjump_to_other_header   '
              '(parent hdr,backedge)')
        for r in rows:
            print('  %6s %5s %-12s %-10s %-24s %-14s %-10s %-12s %-13s %-8s %s'
                  % (r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11]))
    return rv


RegionAnalyzer._cleanup_try_else_in_loop_body = _wrap

for p in sys.argv[1:]:
    print('##### %s' % p)
    pycdc.decompile_pyc(p)
print('=== probe done (%d pycs)' % (len(sys.argv) - 1))
