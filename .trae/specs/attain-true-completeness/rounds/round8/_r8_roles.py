# -*- coding: utf-8 -*-
"""R8 probe: dump CFG blocks + block roles for a pyc (module or nested code)."""
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
analyzer.analyze()
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    try:
        role = analyzer.get_block_role(b)
    except Exception as e:
        role = 'ERR %s' % e
    last = b.get_last_instruction()
    print('blk@%s role=%s last=%s(%s) succ=%s' % (
        b.start_offset, role, last.opname if last else None,
        last.argval if last else None,
        sorted(s.start_offset for s in b.successors)))
