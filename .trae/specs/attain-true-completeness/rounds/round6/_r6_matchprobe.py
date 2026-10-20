# -*- coding: utf-8 -*-
"""R6 probe: MatchRegion case bodies inside except-handler."""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer, MatchRegion  # noqa: E402

pyc = sys.argv[1]
fname = sys.argv[2]

with open(pyc, 'rb') as f:
    code = marshal.loads(f.read()[16:])

target = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == fname:
        target = c
        break

builder = CFGBuilder()
cfg = builder.build(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

for r in analyzer.regions:
    if not isinstance(r, MatchRegion):
        continue
    print('MATCH entry=%s subject=%s merge=%s blocks=%s' % (
        r.entry.start_offset if r.entry else None,
        r.subject_block.start_offset if getattr(r, 'subject_block', None) else None,
        r.merge_block.start_offset if getattr(r, 'merge_block', None) else None,
        [b.start_offset for b in r.blocks]))
    print('  case_patterns=', r.case_patterns)
    print('  case_bodies=', [[b.start_offset for b in body] for body in r.case_bodies])
    print('  case_body_start_indices=', r.case_body_start_indices)
    print('  case_guards=', r.case_guards)
    for b in r.blocks:
        print('   blk@%s instrs=%s' % (
            b.start_offset,
            [(i.opname, i.argval) for i in b.instructions]))
