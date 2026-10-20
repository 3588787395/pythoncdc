# -*- coding: utf-8 -*-
"""R5 x02 adjudication probe: regions for x02::for_in_match."""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402

with open(r'test_repros\round2\x02_for_deep_hosts.pyc', 'rb') as f:
    code = marshal.loads(f.read()[16:])
target = next(c for c in code.co_consts
              if hasattr(c, 'co_name') and c.co_name == 'for_in_match')

builder = CFGBuilder()
cfg = builder.build(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print('=== regions for for_in_match ===')
for r in analyzer.regions:
    print('REGION %s entry@%s blocks=%s' % (
        type(r).__name__, r.entry.start_offset,
        [b.start_offset for b in getattr(r, 'blocks', [])]))
    for attr in ('condition_block', 'header_block', 'case_blocks',
                 'match_cases', 'has_default'):
        v = getattr(r, attr, None)
        if v is None:
            continue
        if isinstance(v, (list, set)):
            print('   %s=%s' % (attr, [getattr(x, 'start_offset', x) for x in v]))
        else:
            print('   %s=%r' % (attr, v))
print('=== blocks ===')
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    print('BLK@%s..%s succ=%s' % (b.start_offset,
          b.instructions[-1].offset if b.instructions else None,
          [s.start_offset for s in b.successors]))
    print('   ', ' | '.join('%s@%s' % (i.opname, i.offset) for i in b.instructions))
