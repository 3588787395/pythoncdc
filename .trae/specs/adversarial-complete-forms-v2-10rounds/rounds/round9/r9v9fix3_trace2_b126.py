#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B126 分派侧追踪（只读 monkeypatch）：while 体内 98/74/76 的 dispatch/back_edge/postprocess。"""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

G = RegionASTGenerator
TARGET = {48, 64, 74, 76, 78, 98, 120, 122}


def kinds(stmts):
    return [(s.get('type') if isinstance(s, dict) else type(s).__name__)
            for s in (stmts or [])]


_disp = G._loop_dispatch_block


def disp(self, block, region, *a, **kw):
    n0 = len(a[0]) if a else 0
    body_stmts = a[0] if a else []
    r = _disp(self, block, region, *a, **kw)
    if block.start_offset in TARGET:
        print('[DISP] blk@%-4s handled=%s added=%s' %
              (block.start_offset, r, kinds(body_stmts[n0:])))
    return r


G._loop_dispatch_block = disp

_hbe = G._loop_handle_back_edge


def hbe(self, block, region, *a, **kw):
    r = _hbe(self, block, region, *a, **kw)
    if block.start_offset in TARGET:
        print('[HBE] blk@%-4s -> %s' % (block.start_offset, r if not isinstance(r, list) else kinds(r)))
    return r


G._loop_handle_back_edge = hbe

_lpp = G._loop_postprocess


def lpp(self, region, body_stmts, body_blocks_no_header, back_edge_stmts, child_info, back_edge_source_blocks):
    n0 = len(body_stmts)
    nb0 = len(body_blocks_no_header)
    r = _lpp(self, region, body_stmts, body_blocks_no_header, back_edge_stmts, child_info, back_edge_source_blocks)
    print('[LPP] entry=%s new_body=%s pend_before=%s after=%s body=%s'
          % (region.entry.start_offset if region.entry else None,
             kinds(body_stmts[n0:]), nb0, len(body_blocks_no_header), kinds(body_stmts)))
    return r


G._loop_postprocess = lpp

_lgb = G._loop_generate_body


def lgb(self, region, *a, **kw):
    r = _lgb(self, region, *a, **kw)
    if region.entry and region.entry.start_offset in (32, 34):
        print('[LGB] entry=%s -> %s' % (region.entry.start_offset, kinds(r)))
    return r


G._loop_generate_body = lgb

raw = marshal.loads(open(sys.argv[1], 'rb').read()[16:])
from core.cfg import build_cfg  # noqa: E402

cfg = build_cfg(raw)
gen = G(cfg, top_level_code=raw)
print('== generating module %s ==' % raw.co_name)
gen.generate()
print('-> done')
