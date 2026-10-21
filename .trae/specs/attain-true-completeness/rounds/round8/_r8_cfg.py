# -*- coding: utf-8 -*-
"""R8 probe: dump CFG blocks (succ/pred/exception edges)."""
import marshal
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402

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
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    exc = sorted(s.start_offset for s in getattr(b, 'exception_successors', []) or [])
    print('BLK@%s..%s succ=%s exc=%s pred=%s' % (
        b.start_offset,
        b.instructions[-1].offset if b.instructions else None,
        sorted(s.start_offset for s in b.successors), exc,
        sorted(p.start_offset for p in b.predecessors)))
    for i in b.instructions:
        print('   %s %s %s' % (i.offset, i.opname, i.argval))
