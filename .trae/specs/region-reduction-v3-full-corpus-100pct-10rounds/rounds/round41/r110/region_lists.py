# -*- coding: utf-8 -*-
"""region_lists.py -- read-only: the exact member lists of the regions that own @7972..@8588.

usage: python -X utf8 region_lists.py
No pipeline semantics touched (analyzer only, no generator).
"""
import io
import marshal
import os
import sys
import types

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace',
                              line_buffering=True)
MIRROR = 'D:/Temp/r110'
sys.path.insert(0, MIRROR)
os.chdir(MIRROR)
PYC = ('D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/'
       'plugins/plugin_system_event_source/realtime_event_source.pyc')
TARGETS = [7972, 7980, 8166, 8170, 8186, 8256, 8282, 8294, 8306, 8350, 8354, 8400, 8450,
           8544, 8588]
TSET = set(TARGETS)


def find(c, n):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == n:
                return k
            r = find(k, n)
            if r:
                return r


from core.cfg import build_cfg                       # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402

fn = find(marshal.loads(open(PYC, 'rb').read()[16:]), 'clock_worker')
cfg = build_cfg(fn)
an = RegionAnalyzer(cfg)
an.analyze()


def o(x):
    return getattr(x, 'start_offset', x)


for entry in (7164, 7186, 7582, 7604, 7634):
    for r in an.regions:
        if o(getattr(r, 'entry', 0) or 0) != entry:
            continue
        nm = type(r).__name__
        if nm not in ('IfRegion', 'TryExceptRegion', 'LoopRegion'):
            continue
        print('=== %s@%d ===' % (nm, entry))
        for attr in ('blocks', 'then_blocks', 'else_blocks', 'elif_final_else',
                     'chained_compare_blocks'):
            v = getattr(r, attr, None)
            if v is None:
                continue
            offs = sorted(o(b) for b in v)
            hits = [x for x in offs if x in TSET]
            print('  %-24s n=%-3d targets_in=%-3d %s' % (
                attr, len(offs), len(hits),
                ('TARGETS=' + str(hits)) if hits else str(offs)[:150]))
        print('  condition_block=%s merge_block=%s exit=%s' % (
            o(getattr(r, 'condition_block', None) or 0),
            o(getattr(r, 'merge_block', None) or 0),
            o(getattr(r, 'exit', None) or 0)))
