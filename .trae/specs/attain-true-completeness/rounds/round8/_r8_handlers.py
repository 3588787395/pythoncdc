# -*- coding: utf-8 -*-
"""R8 probe: dump _parse_exception_table handler infos for a pyc (module or nested code)."""
import marshal
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402

pyc = sys.argv[1]
fname = sys.argv[2] if len(sys.argv) > 2 else None

with open(pyc, 'rb') as f:
    code = marshal.loads(f.read()[16:])

target = code
if fname:
    found = None
    for c in code.co_consts:
        if isinstance(c, types.CodeType) and c.co_name == fname:
            found = c
            break
    if found is None:
        print('NOT FOUND')
        sys.exit(1)
    target = found

builder = CFGBuilder()
cfg = builder.build(target)
analyzer = RegionAnalyzer(cfg)
infos = analyzer._parse_exception_table()
print('=== handler infos (%d) ===' % len(infos))
for i, inf in enumerate(infos):
    blk = cfg.get_block_by_offset(inf['handler_start'])
    ops = [x.opname for x in blk.instructions] if blk else []
    print('%2d try=[%s,%s) handler=%s type=%s depth=%s ops=%s' % (
        i, inf['try_start'], inf['try_end'], inf['handler_start'],
        inf['handler_type'], inf['depth'], ops))
print('=== raw exception table ===')
for e in cfg.exception_table:
    print(e)
