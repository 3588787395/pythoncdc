#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B126 生成侧追踪（只读 monkeypatch）：追踪 while 体块语句生成与 break 来源。

用法: python r9v9fix3_trace_b126.py <pyc> [func]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

G = RegionASTGenerator
TARGET = {48, 64, 74, 76, 78, 98, 120, 122}

_gbs = G._generate_block_statements


def gbs(self, block, _cjb_parent=None):
    r = _gbs(self, block, _cjb_parent=_cjb_parent)
    if block.start_offset in TARGET:
        kinds = []
        for s in r or []:
            t = s.get('type') if isinstance(s, dict) else type(s).__name__
            extra = ''
            if t == 'Break':
                extra = '<== BREAK'
            elif t == 'Continue':
                extra = '<== CONTINUE'
            elif t in ('While', 'For'):
                extra = '<== %s' % t
            kinds.append('%s%s' % (t, extra))
        print('[GBS] blk@%-4s -> %s' % (block.start_offset, kinds))
    return r


G._generate_block_statements = gbs

_lgw = G._loop_generate_while


def lgw(self, region, skip_store_targets=None):
    print('[LGW>] entry=%s cond=%s hdr=%s be=%s body=%s breaks=%s elseb=%s'
          % (region.entry.start_offset if region.entry else None,
             region.condition_block.start_offset if region.condition_block else None,
             region.header_block.start_offset if getattr(region, 'header_block', None) else None,
             region.back_edge_block.start_offset if getattr(region, 'back_edge_block', None) else None,
             sorted(b.start_offset for b in (region.body_blocks or [])),
             sorted(b.start_offset for b in (region.break_blocks or [])),
             sorted(b.start_offset for b in (region.else_blocks or []))))
    r = _lgw(self, region, skip_store_targets=skip_store_targets)
    body = r.get('body') if isinstance(r, dict) else None
    if isinstance(body, list):
        k = [(s.get('type') if isinstance(s, dict) else type(s).__name__)
             for s in body]
    else:
        k = body
    pre = r.get('pre_stmts') if isinstance(r, dict) else None
    print('[LGW<] entry=%s -> type=%s pre=%s body=%s orelse=%s'
          % (region.entry.start_offset if region.entry else None,
             r.get('type') if isinstance(r, dict) else r,
             [ (s.get('type') if isinstance(s, dict) else type(s).__name__) for s in (pre or []) ],
             k,
             (r.get('orelse') if isinstance(r, dict) else None) and
             [ (s.get('type') if isinstance(s, dict) else type(s).__name__) for s in r.get('orelse') ]))
    return r


G._loop_generate_while = lgw

_ga = G._generate_assert


def ga(self, region, *a, **kw):
    r = _ga(self, region, *a, **kw)
    print('[GASSERT] entry=%s -> %s' % (
        region.entry.start_offset if region.entry else None,
        [(s.get('type') if isinstance(s, dict) else type(s).__name__) for s in r]
        if isinstance(r, list) else r))
    return r


G._generate_assert = ga

pyc = sys.argv[1]
func = sys.argv[2] if len(sys.argv) > 2 else 'assert_deep'

import marshal  # noqa: E402
from core.cfg import build_cfg  # noqa: E402


def find_code(code, name):
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            if c.co_name == name:
                return c
            r = find_code(c, name)
            if r is not None:
                return r
    return None


raw = marshal.loads(open(pyc, 'rb').read()[16:])
code = raw if raw.co_name == func else find_code(raw, func)
cfg = build_cfg(code)
gen = G(cfg)
d = gen.generate()
print('-> done')
