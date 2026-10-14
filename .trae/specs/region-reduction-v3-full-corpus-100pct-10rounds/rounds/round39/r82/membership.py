"""Block-membership census (principle 2 unique ownership / principle 4 parent->child entry).

usage: python -X utf8 membership.py <pyc-abs>            # 只读，不改任何判据
"""
import marshal
import sys

sys.path.insert(0, 'D:/Temp/r82')

from core.cfg import build_cfg                                   # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator     # noqa: E402

PYC = sys.argv[1]
co = marshal.loads(open(PYC, 'rb').read()[16:])


def walk(c, acc, prefix=''):
    acc.append((prefix + c.co_name, c))
    for cst in c.co_consts:
        if isinstance(cst, type(c)):
            walk(cst, acc, prefix + c.co_name + '.')


units = []
walk(co, units)
if len(sys.argv) > 2:
    want = sys.argv[2]
    units = [(n, c) for n, c in units if n == want or n.endswith('.' + want)]
    print('unit filter %r -> %d unit(s)' % (want, len(units)))
tot_regions = 0
tot_blocks = 0
two_owner = 0
zero_owner = 0
held_counts = {}
for name, u in units:
    try:
        cfg = build_cfg(u)
        gen = RegionASTGenerator(cfg, top_level_code=u if u.co_name == '<module>' else None,
                                 parent_code=None if u.co_name == '<module>' else u)
        gen.generate()
        regions = list(getattr(gen, 'regions', None) or [])
        b2r = getattr(gen.region_analyzer, 'block_to_region', {}) or {}
    except Exception as e:
        print('GEN-FAIL %s %r' % (name, e))
        continue
    tot_regions += len(regions)
    blocks = list(b2r.keys())
    tot_blocks += len(blocks)
    for b in blocks:
        n = 0
        for r in regions:
            for f in ('then_blocks', 'else_blocks', 'body_blocks', 'elif_conditions',
                      'elif_final_else'):
                if b in (getattr(r, f, None) or []):
                    n += 1
                    break
            for bl in (getattr(r, 'elif_bodies', None) or []):
                if b in (bl or []):
                    n += 1
                    break
        held_counts[n] = held_counts.get(n, 0) + 1
        if n >= 2:
            two_owner += 1
        elif n == 0:
            zero_owner += 1
print('units=%d regions=%d blocks_in_block_to_region=%d two_owner=%d zero_owner=%d' % (
    len(units), tot_regions, tot_blocks, two_owner, zero_owner))
print('held-distribution =', sorted(held_counts.items()))
