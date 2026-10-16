#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 位A 诊断（只读）：dump 目标 code object 的 LoopRegion 链式条件元数据。

用法：python -X utf8 r9v9fix_diag_b104.py <pyc> [co_name ...]
不写 core/，不改行为（只 monkeypatch 收集后原样调用）。
"""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)

from core.cfg import build_cfg  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer, RegionType  # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

pyc = sys.argv[1]
want = set(sys.argv[2:])

_orig_loop = RegionAnalyzer._identify_loop_regions


def wrapped(self, *a, **kw):
    regions = _orig_loop(self, *a, **kw)
    try:
        co = getattr(getattr(self, 'cfg', None), 'code', None)
        coname = getattr(co, 'co_name', '?')
        if not want or coname in want:
            for r in regions:
                if getattr(r, 'region_type', None) == RegionType.WHILE_LOOP:
                    md = getattr(r, 'metadata', {}) or {}
                    print('== LOOP co=%s entry@%s hdr@%s cond@%s be@%s cc=%s ops=%s chainn=%d mixedtail=%s mixedlead=%s'
                          % (coname,
                             getattr(r, 'entry', None) and r.entry.start_offset,
                             r.header_block and r.header_block.start_offset,
                             r.condition_block and r.condition_block.start_offset,
                             r.back_edge_block and r.back_edge_block.start_offset,
                             md.get('is_chained_compare_cond'),
                             md.get('chained_compare_ops'),
                             len(getattr(r, 'condition_chain_blocks', None) or []),
                             len(md.get('cc_mixed_cond_tail_blocks') or []),
                             len(md.get('cc_mixed_cond_lead_blocks') or [])))
                    for i, b in enumerate(r.body_blocks or []):
                        il = [x.opname for x in b.instructions]
                        print('   body[%d] @%d %s' % (i, b.start_offset, il))
                    for b in (getattr(r, 'condition_chain_blocks', None) or []):
                        il = [x.opname for x in b.instructions]
                        print('   chain @%d %s' % (b.start_offset, il))
    except Exception as e:
        print('DIAG ERR %r' % (e,))
    return regions


RegionAnalyzer._identify_loop_regions = wrapped

raw = marshal.loads(open(pyc, 'rb').read()[16:])
cfg = build_cfg(raw)
gen = RegionASTGenerator(cfg, top_level_code=raw if raw.co_name == '<module>' else None)
gen.generate()
print('done')
