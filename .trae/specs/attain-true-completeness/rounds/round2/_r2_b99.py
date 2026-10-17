#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: probe B99 prefix absorption for a JIFOR anchor. usage: _r2_b99.py <pyc> <fn> <anchor>"""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_analyzer import FORWARD_CONDITIONAL_JUMP_OPS, SHORT_CIRCUIT_JUMP_OPS


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


pyc = sys.argv[1]
name = sys.argv[2]
anchor_off = int(sys.argv[3])
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])
targets = []
find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)

start_block = None
for b in cfg.get_blocks_in_order():
    if b.start_offset == anchor_off:
        start_block = b
print('anchor block@%d instrs=%s' % (start_block.start_offset,
      [(i.offset, i.opname, i.argval) for i in start_block.instructions]))
last = start_block.get_last_instruction()
print('anchor last=%s argval=%r in_sc=%s' % (last.opname, last.argval,
                                             last.opname in SHORT_CIRCUIT_JUMP_OPS))
ft = None
for s in start_block.conditional_successors:
    print('  cond_succ @%d' % s.start_offset)
    if s.start_offset != last.argval:
        ft = s
print('ft=@%s' % (ft.start_offset if ft else None))
for p in start_block.predecessors:
    pl = p.get_last_instruction()
    print('pred @%d last=%s argval=%r' % (p.start_offset, pl.opname, pl.argval))
    if pl.opname in FORWARD_CONDITIONAL_JUMP_OPS and pl.argval is not None:
        tgt = cfg.get_block_by_offset(pl.argval)
        print('   pl target=@%s is_ft=%s' % (tgt.start_offset if tgt else None, tgt is ft))
