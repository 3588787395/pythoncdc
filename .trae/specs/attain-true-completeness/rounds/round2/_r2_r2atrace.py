#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 debug: trace _b104r2_absorb_mixed_cc_chain args during analyze.
usage: _r2_r2atrace.py <pyc> <fn>
"""
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
from core.cfg import region_analyzer as RA

pyc = sys.argv[1]
name = sys.argv[2]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])
targets = []


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)

_orig = RA.RegionAnalyzer._b104r2_absorb_mixed_cc_chain


def traced(self, condition_block, header, body):
    print('R2A called: cond=@%s header=@%s body=%s' % (
        condition_block.start_offset if condition_block else None,
        header.start_offset if header else None,
        sorted(b.start_offset for b in body)))
    r = _orig(self, condition_block, header, body)
    print('R2A -> %s' % (None if r is None else {
        k: ([b.start_offset for b in v] if isinstance(v, list) else
            (v.start_offset if hasattr(v, 'start_offset') else v))
        for k, v in r.items()}))
    return r


RA.RegionAnalyzer._b104r2_absorb_mixed_cc_chain = traced
gen = RegionASTGenerator(cfg, top_level_code=None)
gen.region_analyzer.analyze()
RA.RegionAnalyzer._b104r2_absorb_mixed_cc_chain = _orig
