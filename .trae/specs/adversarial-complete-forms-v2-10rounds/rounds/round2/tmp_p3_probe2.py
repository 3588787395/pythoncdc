#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时探针2：对 CAssign 类体 code object 直接跑 generate，记录路径命中。"""
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


def find(code, name):
    if code.co_name == name:
        return code
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            r = find(c, name)
            if r is not None:
                return r
    return None


cls = find(code, sys.argv[2] if len(sys.argv) > 2 else 'CAssign')
cfg = build_cfg(cls)
ra = RegionAnalyzer(cfg, cls)
regions = ra.analyze()
gen = RegionASTGenerator(cfg, cls)
gen.regions = regions

_orig_gb = RegionASTGenerator._generate_block_statements
_orig_gr = RegionASTGenerator._generate_region
_orig_gbs = RegionASTGenerator._generate_basic_region


def p_gb(self, block, parent=None):
    res = _orig_gb(self, block, parent)
    print('[gbs] block=%s -> %s' % (block.start_offset, str(res)[:400]))
    return res


def p_gr(self, region, skip=None):
    res = _orig_gr(self, region, skip)
    print('[gr] %s entry=%s -> %s' % (region.region_type.name,
                                      region.entry.start_offset if region.entry else None,
                                      str(res)[:400]))
    return res


RegionASTGenerator._generate_block_statements = p_gb
RegionASTGenerator._generate_region = p_gr
out = gen.generate()
print('result:', str(out)[:1500])
