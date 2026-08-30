# -*- coding: utf-8 -*-
"""Debug: what makes offset 58 a block leader in w1/w2?"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
sys.path.insert(0, r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_32\repair_engineer")
import nop_marker2  # noqa: E402

from core.cfg.cfg_builder import CFGBuilder

for fn in (nop_marker2.w1, nop_marker2.w2):
    co = fn.__code__
    b = CFGBuilder()
    b.build(co)
    print("=" * 60)
    print(fn.__name__, "jump_targets:", sorted(x for x in b.jump_targets if x < 120))
    print("is_jump_target flags:")
    for instr in b.instructions:
        if instr.offset < 120 and instr.opname not in ("CACHE",):
            print("  %4d %-28s jt=%s" % (instr.offset, instr.opname, instr.is_jump_target))
