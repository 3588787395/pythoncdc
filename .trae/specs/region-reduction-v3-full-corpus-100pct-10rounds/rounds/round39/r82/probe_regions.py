"""Read-only region census probe: dump IfRegion/BoolOpRegion data for a code object.

usage: python -X utf8 probe_regions.py <pyc-abs> <lo-offset> <hi-offset>
"""
import marshal
import sys

sys.path.insert(0, 'D:/Temp/r82')

from core.cfg import build_cfg                       # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

PYC = sys.argv[1]
LO = int(sys.argv[2])
HI = int(sys.argv[3])
ALL = '--all' in sys.argv

co = marshal.loads(open(PYC, 'rb').read()[16:])


def find(c, name):
    for x in c.co_consts:
        if isinstance(x, type(c)) and x.co_name == name:
            return x
    for x in c.co_consts:
        if isinstance(x, type(c)):
            r = find(x, name)
            if r:
                return r


cw = find(co, 'clock_worker')
cfg = build_cfg(cw)
gen = RegionASTGenerator(cfg, parent_code=cw, top_level_code=None)
gen.generate()
regions = gen.regions


def off(b):
    return getattr(b, 'start_offset', None)


def in_range(r):
    vals = [off(getattr(r, f, None)) for f in
            ('entry_block', 'condition_block', 'header_block', 'merge_block')]
    for f in ('then_blocks', 'else_blocks', 'body_blocks', 'elif_conditions', 'elif_final_else'):
        for x in getattr(r, f, None) or []:
            if isinstance(x, list):
                for y in x:
                    vals.append(off(y))
            else:
                vals.append(off(x))
    for ch in (getattr(r, 'inline_boolop_chains', None) or {}).values():
        for b in ch.get('blocks', []):
            vals.append(off(b))
    return any(v is not None and LO <= v <= HI for v in vals), vals


print('regions=%d' % len(regions))
for r in regions:
    entry = off(getattr(r, 'entry_block', None))
    hit, vals = in_range(r)
    if not hit and not ALL:
        continue
    if not hit:
        print('--- %s entry=%s (range-hit via %s)' % (type(r).__name__, entry,
              [v for v in vals if v is not None and LO <= v <= HI]))
    cond = off(getattr(r, 'condition_block', None))
    print('--- %s entry=%s cond=%s type=%s' % (type(r).__name__, entry, cond,
                                               getattr(r, 'region_type', None)))
    for f in ('then_blocks', 'else_blocks', 'body_blocks', 'header_block',
              'merge_block', 'elif_conditions', 'elif_bodies', 'elif_final_else',
              'back_edge_block'):
        if hasattr(r, f):
            v = getattr(r, f)
            if isinstance(v, list):
                print('    %-16s = %s' % (f, [off(x) for x in v]))
            else:
                print('    %-16s = %s' % (f, off(v)))
    ibc = getattr(r, 'inline_boolop_chains', None)
    if ibc:
        for k, ch in ibc.items():
            print('    IBC key_id=%d op=%s blocks=%s extra=%s' % (
                k, ch.get('op'), [off(b) if not isinstance(b, int) else b for b in ch.get('blocks', [])],
                {kk: vv for kk, vv in ch.items() if kk not in ('blocks', 'op')}))
