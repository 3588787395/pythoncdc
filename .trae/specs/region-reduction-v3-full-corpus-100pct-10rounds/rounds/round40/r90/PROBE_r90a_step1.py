# -*- coding: utf-8 -*-
"""PROBE_R90A_step1 — read-only census of the analyzer's own chained-compare machinery over a
chosen code object, plus the loop-condition structural facts.

Nothing here mutates core bytes: the script only *calls* existing analyzer methods
(_is_chained_compare_header / _detect_chained_compare_pattern) and reads the region tree
produced by the landed analyze().  Products are therefore bit-for-bit unchanged by design;
the byte-identity check is done separately in the fire census.

usage: python -X utf8 PROBE_r90a_step1.py <pyc> <code-object-name-suffix>
"""
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, MIRROR)
sys.path.insert(0, os.path.join(MIRROR, 'core'))

from core.pyc_loader_v2 import load_pyc_file_v2                       # noqa: E402
from core.cfg import build_cfg                                        # noqa: E402
import core.cfg.region_analyzer as ra                                 # noqa: E402
from core.cfg.region_analyzer import (BACKWARD_CONDITIONAL_JUMP_OPS,  # noqa: E402
                                      FORWARD_CONDITIONAL_JUMP_OPS)


def code_objects(root):
    stack = [root]
    while stack:
        c = stack.pop()
        yield c
        for k in c.co_consts:
            if isinstance(k, types.CodeType):
                stack.append(k)


def main():
    pyc, suffix = sys.argv[1], sys.argv[2]
    mod = load_pyc_file_v2(pyc)
    code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
    if hasattr(code, 'to_python_code'):
        code = code.to_python_code()
    target = [c for c in code_objects(code)
              if (getattr(c, 'co_qualname', None) or c.co_name).endswith(suffix)]
    if not target:
        raise SystemExit('code object %r not found' % suffix)
    co = target[0]
    print('[probe] unit=%s instrs=%d' % (co.co_name, len(co.co_code) // 2))

    cfg = build_cfg(co)
    ana = ra.RegionAnalyzer(cfg)
    regions = ana.analyze()
    blocks = cfg.get_blocks_in_order()

    print('\n---- 1. _is_chained_compare_header over every block (evaluations/fires) ----')
    evals = fires = 0
    hits = []
    for b in blocks:
        evals += 1
        try:
            f = ana._is_chained_compare_header(b)
        except Exception as exc:                                  # pragma: no cover
            print('   eval error @%s: %s' % (b.start_offset, exc))
            continue
        if f:
            fires += 1
            hits.append(b)
    print('   evaluations=%d fires=%d headers=%s'
          % (evals, fires, [b.start_offset for b in hits]))

    print('\n---- 2. _detect_chained_compare_pattern on those headers ----')
    for b in hits:
        pat = ana._detect_chained_compare_pattern(b)
        if pat is None:
            print('   @%d -> None (chain NOT declared)' % b.start_offset)
        else:
            print('   @%d -> ops=%s chain_blocks=%s'
                  % (b.start_offset,
                     [o.opname if hasattr(o, 'opname') else str(o) for o in pat.get('ops', [])],
                     [cb.start_offset for cb in pat.get('chain_blocks', [])
                      if hasattr(cb, 'start_offset')] if isinstance(pat.get('chain_blocks'), (list, tuple))
                     else pat.get('chain_blocks')))

    print('\n---- 3. declared chained-compare regions in the region tree ----')
    decl = []
    for r in regions:
        cb = getattr(r, 'chained_compare_blocks', None)
        if cb:
            decl.append(r)
    print('   declared=%d' % len(decl))
    for r in decl:
        print('   %s entry=%s blocks=%s cc_blocks=%s ops=%s'
              % (type(r).__name__,
                 r.entry.start_offset if getattr(r, 'entry', None) else None,
                 sorted(b.start_offset for b in r.blocks),
                 sorted(b.start_offset for b in r.chained_compare_blocks),
                 getattr(r, 'chained_compare_ops', None)))

    print('\n---- 4. loop regions and their condition assembly ----')
    for r in regions:
        if not isinstance(r, ra.LoopRegion):
            continue
        print('   LoopRegion entry=%s cond=%s header=%s back=%s body=%s'
              % (r.entry.start_offset if getattr(r, 'entry', None) else None,
                 r.condition_block.start_offset if getattr(r, 'condition_block', None) else None,
                 r.header_block.start_offset if getattr(r, 'header_block', None) else None,
                 sorted(b.start_offset for b in (r.back_edge_blocks or [])),
                 sorted(b.start_offset for b in (getattr(r, 'body_blocks', None) or []))))

    print('\n---- 5. opcode-pair structural facts on conditional jumps (no names/offsets baked) ----')
    fwd_in, bwd_in = {}, {}
    for b in blocks:
        last = b.get_last_instruction()
        if last is None:
            continue
        op = last.opname
        if op in FORWARD_CONDITIONAL_JUMP_OPS:
            for s in b.conditional_successors:
                fwd_in.setdefault(s.start_offset, []).append(b.start_offset)
        elif op in BACKWARD_CONDITIONAL_JUMP_OPS:
            for s in b.conditional_successors:
                bwd_in.setdefault(s.start_offset, []).append(b.start_offset)
    both = sorted(set(fwd_in) & set(bwd_in))
    print('   targets reached BOTH ways=%s' % both)
    for t in both:
        print('     @%d: forward from %s ; backward from %s' % (t, fwd_in[t], bwd_in[t]))


if __name__ == '__main__':
    main()
