# -*- coding: utf-8 -*-
"""PROBE_R90A_step1b — read-only: run the LANDED while-condition boolop-chain detectors on the
target LoopRegion and show, block by block, which one the ownership guard rejects.

Only calls existing analyzer methods and reads block_to_region.  No bytes are touched.
usage: python -X utf8 PROBE_r90a_step1b.py <pyc> <co-name-suffix>
"""
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, MIRROR)
sys.path.insert(0, os.path.join(MIRROR, 'core'))

from core.pyc_loader_v2 import load_pyc_file_v2                        # noqa: E402
from core.cfg import build_cfg                                        # noqa: E402
import core.cfg.region_analyzer as ra                                 # noqa: E402
from core.cfg.region_analyzer import (FORWARD_CONDITIONAL_JUMP_OPS,   # noqa: E402
                                      SHORT_CIRCUIT_JUMP_OPS)


def code_objects(root):
    stack = [root]
    while stack:
        c = stack.pop()
        yield c
        for k in c.co_consts:
            if isinstance(k, types.CodeType):
                stack.append(k)


def offs(blks):
    return sorted(getattr(b, 'start_offset', b) for b in (blks or []))


def main():
    pyc, suffix = sys.argv[1], sys.argv[2]
    mod = load_pyc_file_v2(pyc)
    code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
    if hasattr(code, 'to_python_code'):
        code = code.to_python_code()
    co = [c for c in code_objects(code)
          if (getattr(c, 'co_qualname', None) or c.co_name).endswith(suffix)][0]
    cfg = build_cfg(co)
    ana = ra.RegionAnalyzer(cfg)
    regions = ana.analyze()
    by_off = {b.start_offset: b for b in cfg.get_blocks_in_order()}

    loops = [r for r in regions if isinstance(r, ra.LoopRegion)
             and r.condition_block is not None]
    print('[probe] %s: LoopRegions with condition_block: %s'
          % (co.co_name, [(r.condition_block.start_offset, r.entry.start_offset,
                            r.header_block.start_offset if r.header_block else None)
                           for r in loops]))

    for loop in loops:
        cb = loop.condition_block
        print('\n==== loop cond=@%d entry=@%d header=@%d' %
              (cb.start_offset, loop.entry.start_offset,
               loop.header_block.start_offset if loop.header_block else -1))
        print('     back_edge=%s body=%s blocks=%s'
              % (offs(loop.back_edge_blocks), offs(loop.body_blocks), offs(loop.blocks)))
        fwd = ana._detect_while_boolop_forward_chain(
            cb, loop, FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS)
        print('     _detect_while_boolop_forward_chain -> %s'
              % (None if fwd is None else [(b.start_offset, o) for b, o in fwd]))
        nest = ana._detect_while_condition_nested_and_or_chain(cb, loop)
        print('     _detect_while_condition_nested_and_or_chain -> %s'
              % (None if nest is None else [(b.start_offset, o) for b, o in nest]))
        full = ana._detect_while_condition_boolop_chain(cb, loop)
        print('     _detect_while_condition_boolop_chain -> %s'
              % (None if full is None else [(b.start_offset, o) for b, o in full]))
        if full:
            print('     owner census of chain blocks (block_to_region):')
            for b, o in full:
                own = ana.block_to_region.get(b)
                print('       @%-5d op=%-4s owner=%s@%s in_body=%s'
                      % (b.start_offset, o, type(own).__name__ if own else None,
                         own.entry.start_offset if own is not None and getattr(own, 'entry', None) else '-',
                         b in loop.body_blocks))
        # the entry-copy legs, read off the CFG only
        print('     legs forward-conditional into header from: %s'
              % sorted(x.start_offset for x in cfg.get_blocks_in_order()
                       if x.get_last_instruction()
                       and x.get_last_instruction().opname in FORWARD_CONDITIONAL_JUMP_OPS
                       and loop.header_block in x.conditional_successors))


if __name__ == '__main__':
    main()
