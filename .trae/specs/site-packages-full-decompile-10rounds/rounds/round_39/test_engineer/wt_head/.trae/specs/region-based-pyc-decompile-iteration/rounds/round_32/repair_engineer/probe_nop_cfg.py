# -*- coding: utf-8 -*-
"""Probe CFG block structure for w1 (plain stmt) vs w2 (for-else) vs w8 (for-else 2 stmts)."""
import os
import sys
import types

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
from core.cfg.cfg_builder import build_cfg

sys.path.insert(0, r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_32\repair_engineer")
import nop_marker2  # noqa: E402


def dump(fn):
    co = fn.__code__
    cfg = build_cfg(co)
    print("=" * 70)
    print(fn.__name__)
    for b in cfg.get_blocks_in_order():
        last = b.get_last_instruction()
        instrs = ", ".join("%s(%d)" % (i.opname, i.offset) for i in b.instructions
                           if i.opname not in ("RESUME", "CACHE"))
        print("  block %3d-%3d last=%-28s | %s" % (
            b.start_offset, b.end_offset, last.opname if last else "?",
            instrs))


for fn in (nop_marker2.w1, nop_marker2.w2, nop_marker2.w8):
    dump(fn)
