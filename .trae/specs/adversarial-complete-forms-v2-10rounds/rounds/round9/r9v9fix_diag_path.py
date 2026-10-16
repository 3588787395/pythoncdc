#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 位A 诊断2（只读 monkeypatch）：追踪 while 生成路径（正常路 vs IfRegion 恢复路）。"""
import marshal
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)

from core.cfg import build_cfg  # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402
from core.cfg.region_analyzer import LoopRegion, IfRegion  # noqa: E402

G = RegionASTGenerator


def _loop_while_orig(self, region, skip_store_targets=None):
    print('[DBG0] _loop_generate_while entry@%s ccmeta=%s condblk@%s chainn=%d'
          % (region.entry.start_offset if region.entry else None,
             region.metadata.get('is_chained_compare_cond'),
             region.condition_block.start_offset if region.condition_block else None,
             len(region.condition_chain_blocks or [])))
    return G._loop_generate_while_orig(self, region, skip_store_targets=skip_store_targets)


G._loop_generate_while_orig = G._loop_generate_while
G._loop_generate_while = _loop_while_orig


def _detect_orig(self, region):
    r = G._detect_if_region_as_while_loop_orig(self, region)
    if r is not None:
        print('[DBG4] if-as-while recovery FIRED ifentry@%s condblk@%s'
              % (region.entry.start_offset if region.entry else None,
                 getattr(region, 'condition_block', None)
                 and region.condition_block.start_offset))
    return r


G._detect_if_region_as_while_loop_orig = G._detect_if_region_as_while_loop
G._detect_if_region_as_while_loop = _detect_orig


def _combined_orig(self, loop, *a, **kw):
    r = G._build_while_combined_condition_orig(self, loop, *a, **kw)
    print('[DBG5] _build_while_combined_condition loop@%s -> %s'
          % (getattr(loop, 'entry', None) and loop.entry.start_offset,
             r if not isinstance(r, dict) else r.get('type')))
    return r


G._build_while_combined_condition_orig = G._build_while_combined_condition
G._build_while_combined_condition = _combined_orig


def _bacc_orig(self, cond_block, chain_blocks, ops, *a, **kw):
    r = G._build_assert_chained_compare_orig(self, cond_block, chain_blocks, ops, *a, **kw)
    print('[DBG6] _build_assert_chained_compare cond@%s chain=%s ops=%s -> %s'
          % (cond_block.start_offset if cond_block else None,
             [b.start_offset for b in chain_blocks or []], ops,
             'OK' if r is not None else 'None'))
    return r


G._build_assert_chained_compare_orig = G._build_assert_chained_compare
G._build_assert_chained_compare = _bacc_orig


def _boolop_expr_orig(self, region, *a, **kw):
    r = G._build_boolop_expression_orig(self, region, *a, **kw)
    print('[DBG7] _build_boolop_expression region=%s prefix@%s -> %s'
          % (type(region).__name__,
             getattr(region, 'prefix_block', None)
             and region.prefix_block.start_offset,
             'OK' if r is not None else 'None'))
    return r


G._build_boolop_expression_orig = G._build_boolop_expression
G._build_boolop_expression = _boolop_expr_orig

pyc = sys.argv[1]
raw = marshal.loads(open(pyc, 'rb').read()[16:])
cfg = build_cfg(raw)
gen = RegionASTGenerator(cfg, top_level_code=raw if raw.co_name == '<module>' else None)
gen.generate()
print('done')
