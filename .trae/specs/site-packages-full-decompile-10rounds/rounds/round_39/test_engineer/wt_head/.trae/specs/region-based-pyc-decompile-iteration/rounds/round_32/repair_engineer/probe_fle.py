# -*- coding: utf-8 -*-
"""修复工程师探针3：_find_loop_else FOR 分支内部细节。"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.cfg import region_analyzer as ra


def _fle(self, header, loop_body, loop_type, for_iter_exit=None, condition_block=None):
    body_set = loop_body | {header}
    if loop_type == ra.RegionType.FOR_LOOP and for_iter_exit and for_iter_exit not in body_set:
        # 复刻 break_targets 检测
        break_targets = []
        for block in body_set:
            if block == header:
                continue
            for succ in block.successors:
                if succ not in body_set and succ not in break_targets:
                    block_last = block.get_last_instruction()
                    if block_last and block_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                        if succ != for_iter_exit:
                            break_targets.append(succ)
                    elif block_last and block_last.opname in ra.FORWARD_CONDITIONAL_JUMP_OPS:
                        if succ != for_iter_exit and succ not in body_set:
                            _sl = succ.get_last_instruction()
                            if _sl and _sl.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                                _t = self.cfg.get_block_by_offset(_sl.argval) if _sl.argval is not None else None
                                if _t and _t not in body_set and _t not in break_targets:
                                    break_targets.append(_t)
                            elif _sl and _sl.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                break_targets.append(succ)
        post_else = self.dom_analyzer.find_nearest_common_post_dominator(set(break_targets)) if break_targets else None
        print("[FLE] header=%s fie=%s break_targets=%s post_else=%s" % (
            header.start_offset, for_iter_exit.start_offset,
            [b.start_offset for b in break_targets],
            post_else.start_offset if post_else else None))
    return _orig_fle(self, header, loop_body, loop_type, for_iter_exit, condition_block)


_orig_fle = ra.RegionAnalyzer._find_loop_else
ra.RegionAnalyzer._find_loop_else = _fle

W = os.path.join(ROOT, ".trae", "specs", "region-based-pyc-decompile-iteration",
                 "rounds", "round_32", "test_engineer", "variant_work")
import pycdc
for f in ["F_return_after_finally.pyc", "A2_try_wraps_all.pyc"]:
    print("=" * 20, f)
    pycdc.decompile_pyc(os.path.join(W, f), use_cfg=True)
