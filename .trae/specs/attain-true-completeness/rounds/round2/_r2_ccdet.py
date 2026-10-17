#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: probe chained-compare detection for one function/block."""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

pyc = sys.argv[1]
name = sys.argv[2]
block_off = int(sys.argv[3])
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


targets = []
find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
blk = cfg.get_block_by_offset(block_off)
ra = gen.region_analyzer
print('header?', ra._is_chained_compare_header(blk))
info = ra._detect_chained_compare_pattern(blk)
if info:
    for k, v in info.items():
        try:
            print(' ', k, '=', [b.start_offset for b in v] if isinstance(v, list) and v and hasattr(v[0], 'start_offset') else v)
        except Exception as e:
            print(' ', k, 'ERR', e)
else:
    print('  pattern=None')
