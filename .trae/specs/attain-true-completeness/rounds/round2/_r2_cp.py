#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: trace chain producers. usage: _r2_cp.py <pyc> <fn> [start_filter]"""
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
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


old_start = RegionAnalyzer._detect_boolop_chain_start
old_cond = RegionAnalyzer._detect_boolop_conditional_chain
old_sc = RegionAnalyzer._detect_boolop_short_circuit_chain
old_create = RegionAnalyzer._create_boolop_region_from_chain


def wrap_start(self, block, claimed):
    res = old_start(self, block, claimed)
    print('START block=@%d -> %s' % (block.start_offset,
                                     None if res is None else [(b.start_offset, o) for b, o in res]))
    return res


def wrap_cond(self, start_block, claimed, skip_claimed_check=False, try_scope_exempt=False):
    res = old_cond(self, start_block, claimed, skip_claimed_check, try_scope_exempt)
    print('COND start=@%d skip=%s -> %s' % (start_block.start_offset, skip_claimed_check,
                                            None if res is None else [(b.start_offset, o) for b, o in res]))
    return res


def wrap_sc(self, start_block, skip_first_claimed_check=False, _b99_absorb=True):
    res = old_sc(self, start_block, skip_first_claimed_check, _b99_absorb)
    print('SC start=@%d -> %s' % (start_block.start_offset,
                                  None if res is None else [(b.start_offset, o) for b, o in res]))
    return res


def wrap_create(self, chain, claimed):
    print('CREATE chain=%s' % [(b.start_offset, o) for b, o in chain])
    return old_create(self, chain, claimed)


RegionAnalyzer._detect_boolop_chain_start = wrap_start
RegionAnalyzer._detect_boolop_conditional_chain = wrap_cond
RegionAnalyzer._detect_boolop_short_circuit_chain = wrap_sc
RegionAnalyzer._create_boolop_region_from_chain = wrap_create

pyc = sys.argv[1]
name = sys.argv[2]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])
targets = []
find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
gen.region_analyzer.analyze()
