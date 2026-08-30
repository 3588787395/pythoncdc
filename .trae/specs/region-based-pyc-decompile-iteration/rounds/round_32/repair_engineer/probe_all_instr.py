# -*- coding: utf-8 -*-
"""Print ALL instructions with indices around 46-62."""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
sys.path.insert(0, r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_32\repair_engineer")
import nop_marker2  # noqa: E402

from core.cfg.cfg_builder import CFGBuilder as CB

fn = nop_marker2.w1
b = CB()
b.build(fn.__code__)
instrs = b.instructions
for i, instr in enumerate(instrs):
    print("idx=%3d off=%4d op=%-28s jt=%s" % (i, instr.offset, instr.opname, instr.is_jump_target))
