#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trace phantom While(False) block source for b70a wbc.

usage: python _r5_trace_b70a2.py <pyc> <qualname>
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


def _has_phantom(node):
    if isinstance(node, dict):
        if node.get('type') == 'While' and isinstance(node.get('test'), dict) \
                and node['test'].get('type') == 'Constant' and node['test'].get('value') is False:
            return True
        return any(_has_phantom(v) for v in node.values())
    if isinstance(node, list):
        return any(_has_phantom(v) for v in node)
    return False


_o_gbs = RegionASTGenerator._generate_block_statements
_o_gi = RegionASTGenerator._generate_if


def gbs(self, block, *a, **kw):
    pre = block.start_offset in self.generated_blocks
    res = _o_gbs(self, block, *a, **kw)
    if TARGET in cname(self) and _has_phantom(res):
        print('PHANTOM block@%s pre_generated=%s owner=%s -> %r' % (
            block.start_offset, pre,
            type(self.region_analyzer.get_region_for_block(block)).__name__ if self.region_analyzer.get_region_for_block(block) else None,
            res))
    return res


def gi(self, region, *a, **kw):
    ent = getattr(getattr(region, 'entry', None), 'start_offset', None)
    res = _o_gi(self, region, *a, **kw)
    if TARGET in cname(self) and ent in (66, 34):
        print('GENIF@%s then=%s else=%s -> %r' % (
            ent,
            [b.start_offset for b in region.then_blocks],
            [b.start_offset for b in region.else_blocks],
            res))
    return res


RegionASTGenerator._generate_block_statements = gbs
RegionASTGenerator._generate_if = gi

src = pycdc.decompile_pyc(sys.argv[1])
for i, line in enumerate(src.splitlines(), 1):
    print('%3d %s' % (i, line))
