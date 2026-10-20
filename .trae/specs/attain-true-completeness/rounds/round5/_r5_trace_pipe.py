#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trace actual pycdc pipeline emissions for a target function.

usage: python _r5_trace_pipe.py <pyc> <qualname-substr> [off1,off2,...]
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
WATCH = set()
if len(sys.argv) > 3 and sys.argv[3]:
    for p in sys.argv[3].split(','):
        WATCH.add(int(p))


def code_name(self):
    try:
        return self.cfg.code.co_qualname or self.cfg.code.co_name
    except Exception:
        return ''


def sumz(x, depth=0):
    if depth > 3:
        return '...'
    if x is None:
        return 'None'
    if isinstance(x, list):
        return '[%s]' % ', '.join(sumz(i, depth + 1) for i in x)
    if isinstance(x, dict):
        t = x.get('type')
        if t == 'Return':
            return 'Return(%s)' % sumz(x.get('value'), depth + 1)
        if t in ('Assign', 'AnnAssign'):
            return '%s(%s <- %s)' % (t, sumz(x.get('targets') or x.get('target'), depth + 1),
                                     sumz(x.get('value'), depth + 1))
        if t in ('If', 'While'):
            return '%s(test=%s, body=%s, else=%s)' % (
                t, sumz(x.get('test'), depth + 1), sumz(x.get('body'), depth + 1),
                sumz(x.get('orelse'), depth + 1))
        if t == 'With':
            return 'With(items=%s, body=%s)' % (len(x.get('items') or []), sumz(x.get('body'), depth + 1))
        if t == 'Match':
            return 'Match(cases=%s)' % sumz(x.get('cases'), depth + 1)
        if t == 'Expr':
            return 'Expr(%s)' % sumz(x.get('value'), depth + 1)
        if t == 'Call':
            return 'Call(%s, args=%s)' % (sumz(x.get('func'), depth + 1), sumz(x.get('args'), depth + 1))
        if t == 'Constant':
            return 'Const(%r)' % (x.get('value'),)
        return str(t)
    return repr(x)


_o_gbs = RegionASTGenerator._generate_block_statements
_o_with = RegionASTGenerator._generate_with
_o_match = RegionASTGenerator._generate_match
_o_region = RegionASTGenerator._generate_region


def gbs(self, block, *a, **kw):
    res = _o_gbs(self, block, *a, **kw)
    if block is not None and block.start_offset in WATCH and TARGET in code_name(self):
        print('GBS @%s -> %s' % (block.start_offset, sumz(res)))
    return res


def gw(self, region):
    res = _o_with(self, region)
    if TARGET in code_name(self):
        e = getattr(getattr(region, 'entry', None), 'start_offset', None)
        print('WITH @%s -> %s' % (e, sumz(res)))
    return res


def gm(self, region):
    res = _o_match(self, region)
    if TARGET in code_name(self):
        e = getattr(getattr(region, 'entry', None), 'start_offset', None)
        print('MATCH @%s -> %s' % (e, sumz(res)))
    return res


def gr(self, region, *a, **kw):
    res = _o_region(self, region, *a, **kw)
    if TARGET in code_name(self):
        e = getattr(getattr(region, 'entry', None), 'start_offset', None)
        print('REGION %s @%s -> %s' % (type(region).__name__, e, sumz(res)))
    return res


RegionASTGenerator._generate_block_statements = gbs
RegionASTGenerator._generate_with = gw
RegionASTGenerator._generate_match = gm
RegionASTGenerator._generate_region = gr

src = pycdc.decompile_pyc(sys.argv[1])
for i, line in enumerate(src.splitlines(), 1):
    print('%3d %s' % (i, line))
