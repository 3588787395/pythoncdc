# -*- coding: utf-8 -*-
"""阶段级追踪：目标函数各归约阶段后区域的存留与块归属变化。"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.cfg import region_analyzer as ra

_cur_name = {"n": None}
_orig_try = ra.RegionAnalyzer._identify_try_except_regions
_orig_coalesce = ra.RegionAnalyzer._coalesce_split_try_except_finally_regions
_orig_empty = ra.RegionAnalyzer._identify_empty_body_finally_regions
_orig_loop = ra.RegionAnalyzer._identify_loop_regions
_orig_cond = ra.RegionAnalyzer._identify_conditional_regions


def _snap(tag, analyzer, regions):
    if _cur_name["n"] not in ('order_response_order_update', 'trade_response_order_update'):
        return regions
    print("--[%s %s]--" % (_cur_name["n"], tag))
    for r in regions:
        offs = sorted(b.start_offset for b in (r.blocks or []))
        print("   %-16s entry=%s nblocks=%d %s" % (
            type(r).__name__, getattr(r.entry, 'start_offset', '?'),
            len(r.blocks or []), offs[:12]))
    owned = {}
    for off, r in analyzer.block_to_region.items():
        owned.setdefault(type(r).__name__, []).append(off)
    for k, v in owned.items():
        print("   block_to_region[%s]: %s" % (k, sorted(v)[:14]))
    return regions


def p_try(self):
    return _snap("try", self, _orig_try(self))


def p_coalesce(self, try_regions):
    return _snap("coalesce", self, _orig_coalesce(self, try_regions))


def p_empty(self, try_regions):
    return _snap("empty_finally", self, _orig_empty(self, try_regions))


def p_loop(self):
    return _snap("loop", self, _orig_loop(self))


def p_cond(self, **kw):
    return _snap("cond", self, _orig_cond(self, **kw))


def patched_generate(self):
    _cur_name["n"] = getattr(getattr(self.cfg, 'code', None), 'co_name', None)
    return _og(self)


ra.RegionAnalyzer._identify_try_except_regions = p_try
ra.RegionAnalyzer._identify_loop_regions = p_loop
ra.RegionAnalyzer._identify_conditional_regions = p_cond

from core.cfg.region_ast_generator import RegionASTGenerator
_og = RegionASTGenerator.generate
RegionASTGenerator.generate = patched_generate

import pycdc
pycdc.decompile_pyc(
    r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc",
    use_cfg=True)
