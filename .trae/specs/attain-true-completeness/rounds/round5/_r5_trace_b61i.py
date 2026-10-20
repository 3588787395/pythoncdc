#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trace B61i with-hosted match merge emission for g2a/g2b.

usage: python _r5_trace_b61i.py <pyc> <qualname-substr>
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


_o_gbs = RegionASTGenerator._generate_block_statements
_o_with = RegionASTGenerator._generate_with
_o_match = RegionASTGenerator._generate_match


def gbs(self, block, *a, **kw):
    res = _o_gbs(self, block, *a, **kw)
    if block is not None and block.start_offset in (274, 296) and TARGET in cname(self):
        print('GBS @%s gen_before=%s -> %r' % (
            block.start_offset,
            block in self.generated_blocks,
            res))
    return res


def gw(self, region):
    gen_before = set(self.generated_blocks)
    res = _o_with(self, region)
    if TARGET in cname(self):
        e = getattr(getattr(region, 'entry', None), 'start_offset', None)
        if e in (0, 74):
            b296 = self.cfg.get_block_by_offset(296)
            print('WITH @%s body_end=%r merge_marked_after=%s gen_new=%s' % (
                e, getattr(region, 'body_offset_end', None),
                b296 in self.generated_blocks,
                sorted(b.start_offset for b in (set(self.generated_blocks) - gen_before))))
            print('  RESULT=%r' % (res,))
    return res


def gm(self, region):
    res = _o_match(self, region)
    if TARGET in cname(self):
        e = getattr(getattr(region, 'entry', None), 'start_offset', None)
        if e == 32:
            b296 = self.cfg.get_block_by_offset(296)
            print('MATCH @%s merge=@%s marked=%s -> %r' % (
                e,
                getattr(getattr(region, 'merge_block', None), 'start_offset', None),
                b296 in self.generated_blocks, res))
    return res


RegionASTGenerator._generate_block_statements = gbs
RegionASTGenerator._generate_with = gw
RegionASTGenerator._generate_match = gm

src = pycdc.decompile_pyc(sys.argv[1])
for i, line in enumerate(src.splitlines(), 1):
    print('%3d %s' % (i, line))
