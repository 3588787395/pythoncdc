# -*- coding: utf-8 -*-
"""打桩 RegionASTGenerator.generate，仅对目标函数 dump 全部区域结构。"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator

TARGETS = {"order_response_order_update", "trade_response_order_update"}
_orig_generate = RegionASTGenerator.generate


def patched(self):
    name = getattr(getattr(self.cfg, 'code', None), 'co_name', None)
    if name in TARGETS:
        print("#" * 70)
        print("FUNC:", name)
        orig_ar = RegionASTGenerator._generate_region
        cnt = {'n': 0}

        def ar(gen, region, *a, **kw):
            blocks = list(getattr(region, 'blocks', []) or [])
            offs = sorted(getattr(b, 'start_offset', -1) for b in blocks)
            cnt['n'] += 1
            print('%-26s blocks=%s' % (type(region).__name__, offs))
            return orig_ar(gen, region, *a, **kw)

        RegionASTGenerator._generate_region = ar
        try:
            return _orig_generate(self)
        finally:
            RegionASTGenerator._generate_region = orig_ar
            print("=== regions:", cnt['n'])
    return _orig_generate(self)


RegionASTGenerator.generate = patched

from pycdc import decompile_pyc
decompile_pyc(r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc", use_cfg=True)
