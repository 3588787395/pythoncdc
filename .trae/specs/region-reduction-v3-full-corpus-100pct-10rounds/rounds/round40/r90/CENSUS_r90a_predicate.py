# -*- coding: utf-8 -*-
"""CENSUS_R90A_predicate — fire census of the identification-time predicate a
duplicated-while-test rule would key on, evaluated with the LANDED analyzer (read-only).

P(L) for a LoopRegion L with a non-None condition_block:
    (a) L's header block receives a FORWARD conditional jump from a block that is NOT one of
        L's own blocks   -> an entry-copy leg owned elsewhere; and
    (b) L's header block receives a BACKWARD conditional jump from a block inside L's body
        -> a latch-copy leg.
fire := (a) and (b).

Also records, per fire, the owner census of the forward-leg blocks, using the stated rule:
  zero_owner  : block_to_region[b] is None            (unclaimed: walk may absorb it)
  two_owner   : b claimed by a region AND b is a leg of another loop's condition chain
                (claimed by the enclosing LoopRegion while also being an entry leg here)
  one_owner   : claimed by exactly this loop itself
usage: python -X utf8 CENSUS_r90a_predicate.py <budget_sec> <pathlist> [start]
"""
import os
import sys
import time
import types

MIRROR = 'D:/Temp/r90'
sys.path.insert(0, MIRROR)
sys.path.insert(0, os.path.join(MIRROR, 'core'))

from core.pyc_loader_v2 import load_pyc_file_v2                        # noqa: E402
from core.cfg import build_cfg                                        # noqa: E402
import core.cfg.region_analyzer as ra                                 # noqa: E402
from core.cfg.region_analyzer import (FORWARD_CONDITIONAL_JUMP_OPS,   # noqa: E402
                                      BACKWARD_CONDITIONAL_JUMP_OPS)

ROOT = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main'


def code_objects(root):
    stack = [root]
    while stack:
        c = stack.pop()
        yield c
        for k in c.co_consts:
            if isinstance(k, types.CodeType):
                stack.append(k)


def census_unit(co):
    cfg = build_cfg(co)
    ana = ra.RegionAnalyzer(cfg)
    regions = ana.analyze()
    blocks = cfg.get_blocks_in_order()
    ev = fires = 0
    details = []
    for r in regions:
        if not isinstance(r, ra.LoopRegion) or r.condition_block is None:
            continue
        ev += 1
        hdr = r.header_block
        if hdr is None:
            continue
        own = {b.start_offset for b in r.blocks}
        body_owns = {b.start_offset for b in (r.body_blocks or [])}
        fwdl = [b.start_offset for b in blocks
                if b.get_last_instruction()
                and b.get_last_instruction().opname in FORWARD_CONDITIONAL_JUMP_OPS
                and hdr in b.conditional_successors and b.start_offset not in own]
        bwdl = [b.start_offset for b in blocks
                if b.get_last_instruction()
                and b.get_last_instruction().opname in BACKWARD_CONDITIONAL_JUMP_OPS
                and hdr in b.conditional_successors and b.start_offset in body_owns]
        if fwdl and bwdl:
            fires += 1
            kinds = []
            for off in fwdl:
                b = [x for x in blocks if x.start_offset == off][0]
                o = ana.block_to_region.get(b)
                if o is None:
                    kinds.append('@%d:zero_owner' % off)
                elif o is r:
                    kinds.append('@%d:one_owner' % off)
                else:
                    kinds.append('@%d:two_owner(%s@%s)'
                                 % (off, type(o).__name__,
                                    o.entry.start_offset if getattr(o, 'entry', None) else -1))
            details.append('unit=%s loop cond=@%d header=@%d forward-legs-outside=%s '
                           'latch-legs-in-body=%s owners=%s'
                           % (co.co_name, r.condition_block.start_offset, hdr.start_offset,
                              fwdl, bwdl, ' '.join(kinds)))
    return ev, fires, details


def main():
    budget = float(sys.argv[1])
    paths = [l.strip() for l in open(sys.argv[2], encoding='utf-8') if l.strip()]
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    t0 = time.time()
    tot_ev = tot_fire = 0
    cursor = start
    for cursor in range(start, len(paths)):
        if time.time() - t0 > budget:
            print('BUDGET NEXT=%d evals=%d fires=%d' % (cursor, tot_ev, tot_fire))
            sys.exit(3)
        rel = paths[cursor]
        if os.path.isabs(rel):
            p = rel
        else:
            p = next((c for c in (os.path.join(ROOT, rel.replace('/', os.sep)),
                                  os.path.join(ROOT, 'site-packages', rel.replace('/', os.sep)))
                      if os.path.isfile(c)), None)
        if p is None:
            print('MISSING %s' % rel)
            continue
        try:
            code = marshal_load(p)
        except Exception as exc:
            print('UNMARSHAL_FAIL %s %s' % (rel, exc))
            continue
        fe = ff = 0
        for co in code_objects(code):
            try:
                ev, fires, det = census_unit(co)
            except Exception as exc:
                print('  ANALYZE_FAIL %s %s: %s' % (rel, co.co_name, exc))
                continue
            fe += ev
            ff += fires
            for d in det:
                print('FIRE %s :: %s :: %s' % (rel, os.path.basename(p), d))
        tot_ev += fe
        tot_fire += ff
        print('FILE %s loop_cond_evaluations=%d fires=%d elapsed=%.0fs' % (rel, fe, ff, time.time() - t0))
    print('DONE files=%d evaluations=%d fires=%d elapsed=%.0fs'
          % (len(paths), tot_ev, tot_fire, time.time() - t0))


def marshal_load(p):
    import marshal
    return marshal.loads(open(p, 'rb').read()[16:])


if __name__ == '__main__':
    main()
