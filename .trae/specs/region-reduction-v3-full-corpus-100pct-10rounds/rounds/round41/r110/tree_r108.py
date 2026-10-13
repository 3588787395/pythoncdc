"""tree_r108.py — read-only structural census: region parentage + who owns each target entry.

usage: python -X utf8 tree_r108.py
"""
import marshal
import sys
import types

sys.path.insert(0, '.')
from core.cfg import build_cfg                                    # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer               # noqa: E402

PYC = ('D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/'
       'plugins/plugin_system_event_source/realtime_event_source.pyc')
TARGETS = [7972, 8294, 8350, 8354, 8400, 8450, 8186, 7634, 7582, 7216, 7270]


def find(c, n):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == n:
                return k
            r = find(k, n)
            if r:
                return r


def o(x):
    return getattr(x, 'start_offset', x)


fn = find(marshal.loads(open(PYC, 'rb').read()[16:]), 'clock_worker')
cfg = build_cfg(fn)
an = RegionAnalyzer(cfg)
an.analyze()

byoff = {}
for r in an.regions:
    if r.entry is not None:
        byoff.setdefault(o(r.entry), []).append(r)

print('--- parentage of target-entry regions ---')
for t in TARGETS:
    for r in byoff.get(t, []):
        p = getattr(r, 'parent', None)
        print('%-18s @%-5d parent=%-22s nchild=%-3d nblk=%d' % (
            type(r).__name__, t,
            ('%s@%d' % (type(p).__name__, o(p.entry))) if p is not None else 'None',
            len(getattr(r, 'children', None) or ()), len(r.blocks or ())))
    if t not in byoff:
        print('@%-5d  (no region with this entry)' % t)

print('--- region tree (parents only, depth<=3) ---')
roots = [r for r in an.regions if getattr(r, 'parent', None) is None]
for r in sorted(roots, key=lambda x: o(x.entry) if x.entry else 0):
    print('ROOT %-18s @%-6s nblk=%d nchild=%d' % (
        type(r).__name__, o(r.entry) if r.entry else '-', len(r.blocks or ()),
        len(getattr(r, 'children', None) or ())))
    for c in (r.children or []):
        print('   KID %-18s @%-6s nblk=%d nchild=%d' % (
            type(c).__name__, o(c.entry) if c.entry else '-',
            len(c.blocks or ()), len(getattr(c, 'children', None) or ())))

print('--- LoopRegion@5598 body_blocks vs children entries ---')
for r in an.regions:
    if type(r).__name__ == 'LoopRegion' and o(r.entry) == 5598:
        ce = set(o(c.entry) for c in (r.children or []) if c.entry is not None)
        bb = [o(b) for b in (r.body_blocks or [])]
        print('children entries:', sorted(ce))
        print('body_blocks n=%d:' % len(bb), sorted(bb))
        print('IN RANGE body_blocks:', [x for x in sorted(bb) if 7900 <= x <= 8600])
        print('in-range NOT direct-child-entry:',
              [x for x in sorted(bb) if 7900 <= x <= 8600 and x not in ce])
