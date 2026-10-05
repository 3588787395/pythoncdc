#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时追踪：monkeypatch _generate_assert / _generate_region 记录调用流。"""
import sys
ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

module = load_pyc_file_v2(sys.argv[1])
code = module.code
if hasattr(code, 'get'):
    code = code.get()
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()
cfg = build_cfg(code)
ra = RegionAnalyzer(cfg, code)
regions = ra.analyze()
gen = RegionASTGenerator(cfg, top_level_code=code)
gen.regions = regions

_orig_ga = RegionASTGenerator._generate_assert
_orig_gr = RegionASTGenerator._generate_region


def patched_ga(self, region, skip_store_targets=None):
    pre = self._take_assert_prefix_stmts(region)
    res = _orig_ga(self, region, skip_store_targets)
    print('[assert] entry=%s pre=%s res=%s' % (
        region.entry.start_offset if region.entry else None,
        pre, str(res)[:120]))
    return res


def patched_gr(self, region, skip_store_targets=None):
    res = _orig_gr(self, region, skip_store_targets)
    print('[region] %s entry=%s -> %s' % (
        region.region_type.name,
        region.entry.start_offset if region.entry else None,
        str(res)[:150]))
    return res


RegionASTGenerator._generate_assert = patched_ga
RegionASTGenerator._generate_region = patched_gr
out = gen.generate()
import json
print(json.dumps(out, default=str)[:2000])
