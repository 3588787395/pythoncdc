# -*- coding: utf-8 -*-
"""Trace is_leader computation for w1/w2."""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
sys.path.insert(0, r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_32\repair_engineer")
import nop_marker2  # noqa: E402

from core.cfg.cfg_builder import CFGBuilder, CFGBuilder as CB

fn = nop_marker2.w1
co = fn.__code__
b = CB()
b.build(co)
print("jump_targets:", sorted(x for x in b.jump_targets if x < 130))
instrs = b.instructions
for i, instr in enumerate(instrs):
    if instr.offset not in (56, 58, 60) and instr.offset not in (100, 102, 104):
        continue
    prev = instrs[i - 1] if i > 0 else None
    is_leader = (
        instr.offset in b.jump_targets or
        (i > 0 and prev.opname in b.JUMP_INSTRUCTIONS) or
        (i > 0 and prev.opname in b.RETURN_INSTRUCTIONS) or
        (i > 0 and prev.opname in b.RAISE_INSTRUCTIONS) or
        (i > 0 and prev.opname in b.BRANCH_INSTRUCTIONS) or
        (i > 0 and prev.opname == 'RETURN_GENERATOR')
    )
    print("off=%4d op=%-28s prev=%s prev_op=%s leader=%s jt=%s" % (
        instr.offset, instr.opname,
        prev.offset if prev else None, prev.opname if prev else None,
        is_leader, instr.offset in b.jump_targets))
print("--- all blocks ---")
for blk in b.cfg.get_blocks_in_order():
    print("  block %d-%d" % (blk.start_offset, blk.end_offset))
