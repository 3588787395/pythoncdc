# -*- coding: utf-8 -*-
"""修复工程师探针2：追踪 else_blocks 计算路径。"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.cfg import region_analyzer as ra

_orig_find_loop_else = ra.RegionAnalyzer._find_loop_else


def _fle(self, header, loop_body, loop_type, for_iter_exit=None, condition_block=None):
    res, nat = _orig_find_loop_else(self, header, loop_body, loop_type, for_iter_exit, condition_block)
    print("[_find_loop_else] header=%s type=%s for_iter_exit=%s -> else=%s natural=%s" % (
        header.start_offset, loop_type,
        for_iter_exit.start_offset if for_iter_exit else None,
        [b.start_offset for b in res] if res else None,
        nat.start_offset if nat else None))
    return res, nat


ra.RegionAnalyzer._find_loop_else = _fle

_orig_trailing = ra.RegionAnalyzer._check_block_has_trailing_return_none


def _trail(self, block):
    r = _orig_trailing(self, block)
    if block.start_offset >= 550:
        print("[trailing_return_none] blk=%s -> %s" % (block.start_offset, r))
    return r


ra.RegionAnalyzer._check_block_has_trailing_return_none = _trail

W = os.path.join(ROOT, ".trae", "specs", "region-based-pyc-decompile-iteration",
                 "rounds", "round_32", "test_engineer", "variant_work")
import pycdc
pycdc.decompile_pyc(os.path.join(W, "F_return_after_finally.pyc"), use_cfg=True)
