# -*- coding: utf-8 -*-
"""直接调用 _identify_try_except_regions，对比目标与 A2 的 try 区域识别结果。"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.cfg import region_analyzer as ra

_orig = ra.RegionAnalyzer._identify_try_except_regions


def patched(self):
    regions = _orig(self)
    name = getattr(getattr(self.cfg, 'code', None), 'co_name', None)
    if name in ('order_response_order_update', 'trade_response_order_update', 'f'):
        print("### try-regions for %s: %d" % (name, len(regions)))
        for r in regions:
            offs = sorted(b.start_offset for b in (r.blocks or []))
            print("   %s entry=%s blocks=%s" % (type(r).__name__,
                  getattr(r, 'entry', None) and r.entry.start_offset, offs))
    return regions


ra.RegionAnalyzer._identify_try_except_regions = patched

W = os.path.join(ROOT, ".trae", "specs", "region-based-pyc-decompile-iteration",
                 "rounds", "round_32", "test_engineer", "variant_work")

import pycdc

for pyc, label in [
    (r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc", "TARGET"),
    (os.path.join(W, "A2_try_wraps_all.pyc"), "A2"),
]:
    print("=" * 25, label, "=" * 25)
    pycdc.decompile_pyc(pyc, use_cfg=True)
