# -*- coding: utf-8 -*-
"""生成期探针：对比目标与 A2 顶级区域过滤前后的名单及 parent 链。"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.cfg import region_analyzer as ra
from core.cfg.region_ast_generator import RegionASTGenerator

TARGETS = ('order_response_order_update', 'trade_response_order_update', 'f')
_cur = {"n": None}
_og = RegionASTGenerator.generate


def _dump(tag, gen):
    if _cur["n"] not in TARGETS:
        return
    regions = gen.region_analyzer.regions
    print("--[%s %s] regions=%d" % (_cur["n"], tag, len(regions)))
    for r in regions:
        par = getattr(r, 'parent', None)
        print("   %-16s entry=%-4s n=%-3d parent=%s" % (
            type(r).__name__, getattr(r.entry, 'start_offset', '?'),
            len(r.blocks or []),
            type(par).__name__ if par is not None else None))


def patched_generate(self):
    _cur["n"] = getattr(getattr(self.cfg, 'code', None), 'co_name', None)
    # 包一层 analyze 以便在 analyze 后立即 dump
    _an = self.region_analyzer
    _orig_analyze = _an.analyze

    def wrapped_analyze():
        result = _orig_analyze()
        _dump("post-analyze", self)
        return result

    self.region_analyzer.analyze = wrapped_analyze
    try:
        return _og(self)
    except Exception as e:
        print("EXC in generate for", _cur["n"], repr(e))
        raise


RegionASTGenerator.generate = patched_generate

W = os.path.join(ROOT, ".trae", "specs", "region-based-pyc-decompile-iteration",
                 "rounds", "round_32", "test_engineer", "variant_work")

import pycdc

for pyc, label in [
    (os.path.join(W, "A2_try_wraps_all.pyc"), "A2"),
    (r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc", "TARGET"),
]:
    print("=" * 25, label, "=" * 25)
    pycdc.decompile_pyc(pyc, use_cfg=True)
