#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时探针：对 m01 模块跑 assert 前缀切分链路。"""
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

for r in regions:
    if r.region_type.name == 'ASSERT':
        cb = r.condition_block
        print('ASSERT region condition_block:', cb.start_offset if cb else None)
        prefix = gen._split_block_condition_prefix(cb)
        print('prefix instrs:', [(i.opname, i.argval) for i in prefix])
        gen._collect_assert_prefix_stmts(r)
        stmts = gen._take_assert_prefix_stmts(r)
        print('prefix stmts:', stmts)
        ast = gen._generate_assert(r)
        print('assert ast:', ast)
