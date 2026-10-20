#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trace _filter_if_blocks_in_with for b70a.

usage: python _r5_trace_b70a.py <pyc> <qualname>
"""
import io
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pycdc
from core.cfg.region_ast_generator import RegionASTGenerator

TARGET = sys.argv[2]


def cname(self):
    try:
        return self.cfg.code.co_qualname or self.cfg.code.co_name
    except Exception:
        return ''


_o_f = RegionASTGenerator._filter_if_blocks_in_with
_o_gw = RegionASTGenerator._generate_with
_o_gi = RegionASTGenerator._generate_if


def f(self, if_region, with_region):
    res = _o_f(self, if_region, with_region)
    if TARGET in cname(self):
        print('FILTER if@%s with@%s loop=%s -> then=%s else=%s break=%s cont=%s' % (
            getattr(getattr(if_region, 'entry', None), 'start_offset', None),
            getattr(getattr(with_region, 'entry', None), 'start_offset', None),
            getattr(getattr(self._current_loop, 'entry', None), 'start_offset', None),
            [b.start_offset for b in res[0]], [b.start_offset for b in res[1]],
            res[2], res[3]))
        if res[3]:
            print('  backjump@2->header:', self._backjump_reaches_loop_header(
                self.cfg.get_block_by_offset(2)))
            for b in if_region.then_blocks:
                print('  tb@%s role=%s wc=%s' % (
                    b.start_offset, self.region_analyzer.get_block_role(b),
                    self.region_analyzer._is_with_exit_cleanup(b)))
    return res


def gi(self, region, *a, **kw):
    res = _o_gi(self, region, *a, **kw)
    if TARGET in cname(self) and getattr(getattr(region, 'entry', None), 'start_offset', None) in (66, 34):
        print('IF@%s -> %r' % (region.entry.start_offset, res))
    return res


def gw(self, region):
    res = _o_gw(self, region)
    if TARGET in cname(self):
        print('WITH@%s -> %r' % (getattr(getattr(region, 'entry', None), 'start_offset', None), res))
    return res


RegionASTGenerator._filter_if_blocks_in_with = f
RegionASTGenerator._generate_if = gi
RegionASTGenerator._generate_with = gw

src = pycdc.decompile_pyc(sys.argv[1])
for i, line in enumerate(src.splitlines(), 1):
    print('%3d %s' % (i, line))
