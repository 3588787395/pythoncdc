#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Trace RegionASTGenerator emissions for selected blocks/regions.

usage: python _r5_trace_gen.py <pyc> <qualname-substr> [off1,off2,...]
"""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import (RegionASTGenerator, WithRegion,
                                           MatchRegion, IfRegion)

WATCH = set()


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if name in const.co_qualname or name in const.co_name:
                out.append(const)
            find_code(const, name, out)


def summarize(x):
    if x is None:
        return 'None'
    if isinstance(x, list):
        return '[%s]' % ', '.join(summarize(i) for i in x)
    if isinstance(x, dict):
        t = x.get('type')
        if t == 'Return':
            return 'Return(%s)' % summarize(x.get('value'))
        if t in ('Assign', 'AnnAssign'):
            return '%s(%s)' % (t, summarize(x.get('targets') or x.get('target')))
        if t in ('If', 'While'):
            return '%s(test=%s, body=%s, else=%s)' % (
                t, summarize(x.get('test')), summarize(x.get('body')),
                summarize(x.get('orelse')))
        if t == 'Expr':
            return 'Expr(%s)' % summarize(x.get('value'))
        if t == 'Call':
            return 'Call(%s, args=%s)' % (summarize(x.get('func')), summarize(x.get('args')))
        if t == 'Constant':
            return 'Const(%r)' % (x.get('value'),)
        return str(t)
    return repr(x)


_orig_gbs = RegionASTGenerator._generate_block_statements
_orig_with = RegionASTGenerator._generate_with
_orig_match = RegionASTGenerator._generate_match


def gbs(self, block, *a, **kw):
    res = _orig_gbs(self, block, *a, **kw)
    if block is not None and block.start_offset in WATCH:
        print('GBS @%s -> %s' % (block.start_offset, summarize(res)))
    return res


def gw(self, region):
    res = _orig_with(self, region)
    if region.entry is not None and region.entry.start_offset in WATCH:
        print('WITH @%s -> %s' % (region.entry.start_offset, summarize(res)))
    return res


def gm(self, region):
    res = _orig_match(self, region)
    if region.entry is not None and region.entry.start_offset in WATCH:
        print('MATCH @%s -> %s' % (region.entry.start_offset, summarize(res)))
    return res


RegionASTGenerator._generate_block_statements = gbs
RegionASTGenerator._generate_with = gw
RegionASTGenerator._generate_match = gm


def main():
    pyc = sys.argv[1]
    name = sys.argv[2]
    if len(sys.argv) > 3 and sys.argv[3]:
        for p in sys.argv[3].split(','):
            WATCH.add(int(p))
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    targets = []
    find_code(code, name, targets)
    if not targets:
        print('NOT FOUND', name)
        return
    co = targets[-1]
    cfg = build_cfg(co)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    gen.region_analyzer.analyze()
    try:
        tree = gen.generate()
        print('--- top-level AST ---')
        print(summarize(tree))
    except Exception:
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
