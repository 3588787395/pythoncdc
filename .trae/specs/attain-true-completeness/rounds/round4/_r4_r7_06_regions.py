#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 B47 region dump: TernaryRegion layout for r7_06 async ternaries."""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion

pyc = r'test_repros/round7/r7_06_ternary_lambda_await.pyc'
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])

targets = {'t_await_ternary_branches', 't_await_assign_ternary', 't_await_deep_ternary'}
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name in targets:
        print('=' * 72)
        print('FUNC', const.co_name)
        cfg = build_cfg(const)
        ra = RegionAnalyzer(cfg)
        ra.analyze()
        for r in ra.regions:
            if isinstance(r, TernaryRegion):
                def boff(b):
                    return None if b is None else b.start_offset
                print(f"TernaryRegion entry={boff(r.entry)} cond={boff(r.condition_block)} "
                      f"true={boff(getattr(r, 'true_value_block', None))} "
                      f"false={boff(getattr(r, 'false_value_block', None))} "
                      f"merge={boff(r.merge_block)} start={getattr(r, 'start_offset', None)} end={getattr(r, 'end_offset', None)}")
                for nm, b in (('cond', r.condition_block), ('true', getattr(r, 'true_value_block', None)),
                              ('false', getattr(r, 'false_value_block', None)), ('merge', r.merge_block)):
                    if b is None:
                        continue
                    print(f"  [{nm}] @{b.start_offset} succs={[s.start_offset for s in b.successors]} preds={[p.start_offset for p in b.predecessors]}")
                    for ins in b.instructions:
                        print(f"      {ins.offset:4d} {ins.opname} {ins.argval!r}")
