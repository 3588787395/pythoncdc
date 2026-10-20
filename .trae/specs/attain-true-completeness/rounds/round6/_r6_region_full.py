# -*- coding: utf-8 -*-
"""Dump full region attributes for one function."""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

pyc = sys.argv[1]
fname = sys.argv[2]
raw = open(pyc, 'rb').read()
code = marshal.loads(raw[16:])
t = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == fname][0]
cfg = CFGBuilder().build(t)
an = RegionAnalyzer(cfg)
an.analyze()
gen = RegionASTGenerator(cfg)


def off(b):
    return getattr(b, 'start_offset', None)


for r in an.regions:
    print('REGION', type(r).__name__, 'id', id(r))
    for k, v in sorted(vars(r).items()):
        if k in ('parent', 'children'):
            if k == 'parent':
                print('  parent:', type(v).__name__ if v else None)
            else:
                print('  children:', [(type(c).__name__, off(getattr(c, 'entry', None))) for c in (v or [])])
            continue
        if isinstance(v, (list, tuple, set)):
            vals = []
            for x in v:
                if hasattr(x, 'start_offset'):
                    vals.append((type(x).__name__, x.start_offset))
                elif isinstance(x, tuple):
                    vals.append(tuple(off(y) if hasattr(y, 'start_offset') else y for y in x))
                else:
                    vals.append(x)
            print('  %s: %r' % (k, vals))
        elif hasattr(v, 'start_offset'):
            print('  %s:' % k, type(v).__name__, v.start_offset)
        else:
            print('  %s: %r' % (k, v))
    print('  blocks:', [off(b) for b in r.blocks])
    print()
