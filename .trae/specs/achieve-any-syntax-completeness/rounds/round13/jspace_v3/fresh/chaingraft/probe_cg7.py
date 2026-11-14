# probe_cg7.py: 记录 cg7（with 内守卫 + 后续 if/else）的 elif 决策
import sys, os, runpy, types

REPO = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, REPO)
if 'pydot' not in sys.modules:
    stub = types.ModuleType('pydot')
    stub.graph_from_dot_data = lambda *a, **k: []
    stub.Dot = stub.Node = stub.Edge = lambda *a, **k: None
    sys.modules['pydot'] = stub

import core.cfg.region_analyzer as ra

LOG = []


def cls_with(name):
    for n in dir(ra):
        o = getattr(ra, n)
        if isinstance(o, type) and hasattr(o, name):
            return o
    return None


cls = cls_with('_build_elif_region')
orig_build = cls._build_elif_region


def build_wrap(self, *a, **k):
    block = a[0] if a else k.get('block')
    then_blocks = a[1] if len(a) > 1 else k.get('then_blocks')
    else_blocks = a[2] if len(a) > 2 else k.get('else_blocks')
    merge = a[3] if len(a) > 3 else k.get('merge')
    off = getattr(block, 'start_offset', '?')
    LOG.append('BUILD_ELIF block=@%s then=%s else=%s merge=@%s' % (
        off,
        sorted(getattr(b, 'start_offset', -1) for b in (then_blocks or [])),
        sorted(getattr(b, 'start_offset', -1) for b in (else_blocks or [])),
        getattr(merge, 'start_offset', None)))
    r = orig_build(self, *a, **k)
    LOG.append('  -> %s' % (type(r).__name__ if r is not None else None))
    return r


cls._build_elif_region = build_wrap

pyc = sys.argv[1]
out = sys.argv[2]
sys.argv = ['pycdc.py', pyc, '-o', out]
try:
    runpy.run_path(os.path.join(REPO, 'pycdc.py'), run_name='__main__')
except SystemExit:
    pass

with open(out + '.eliflog.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(LOG) if LOG else '(none)')
print('\n'.join(LOG))
