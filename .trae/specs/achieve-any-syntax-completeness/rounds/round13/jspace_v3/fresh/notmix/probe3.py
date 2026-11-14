# -*- coding: utf-8 -*-
"""probe3: instrument _detect_boolop_conditional_chain, then run the real
pycdc pipeline via runpy with fake argv. Records every call's return."""
import sys, os, runpy, types

REPO = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, REPO)

# pydot stub (judge-env style)
if 'pydot' not in sys.modules:
    stub = types.ModuleType('pydot')
    stub.graph_from_dot_data = lambda *a, **k: []
    stub.Dot = stub.Node = stub.Edge = lambda *a, **k: None
    sys.modules['pydot'] = stub

import core.cfg.region_analyzer as ra

LOG = []
_depth = [0]


def find_cls():
    for name in dir(ra):
        obj = getattr(ra, name)
        if isinstance(obj, type) and hasattr(obj, '_detect_boolop_conditional_chain'):
            return obj
    return None


cls = find_cls()
assert cls is not None
orig = cls._detect_boolop_conditional_chain


def wrapper(self, start_block, claimed, *a, **k):
    n = len(LOG)
    depth = _depth[0]
    _depth[0] += 1
    try:
        r = orig(self, start_block, claimed, *a, **k)
    finally:
        _depth[0] -= 1
    so = getattr(start_block, 'start_offset', '?')
    if r is None:
        LOG.append('%sCALL#%d start=@%s -> None' % ('  ' * depth, n, so))
    else:
        LOG.append('%sCALL#%d start=@%s -> %s' % (
            '  ' * depth, n, so,
            [(getattr(b, 'start_offset', '?'), op) for b, op in r]))
    return r


cls._detect_boolop_conditional_chain = wrapper

pyc = sys.argv[1]
out = sys.argv[2]
sys.argv = ['pycdc.py', pyc, '-o', out]
try:
    runpy.run_path(os.path.join(REPO, 'pycdc.py'), run_name='__main__')
except SystemExit:
    pass

print('\n'.join(LOG))
with open(out + '.probelog.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(LOG) if LOG else '(no calls)')
