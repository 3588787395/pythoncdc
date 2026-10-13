"""READ-ONLY dump of blocks/regions for one unit of a pyc.

usage: python -X utf8 dump_r95.py <pyc-abs> <unit> [lo] [hi]
"""
import marshal
import sys
import types

sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.pyc_loader_v2 import load_pyc_file_v2

PYC = sys.argv[1]
UNIT = sys.argv[2]
LO = int(sys.argv[3]) if len(sys.argv) > 3 else 0
HI = int(sys.argv[4]) if len(sys.argv) > 4 else 10 ** 9


def find(c, name):
    for const in c.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            got = find(const, name)
            if got is not None:
                return got
    return None


code = marshal.loads(open(PYC, 'rb').read()[16:])
fn = find(code, UNIT)
if fn is None:
    print('unit not found')
    sys.exit(1)

cfg = build_cfg(fn)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

blocks = cfg.get_blocks_in_order()
print('unit=%s blocks=%d' % (UNIT, len(blocks)))


def offs(bl):
    return sorted(getattr(b, 'start_offset', b) for b in (bl or []))


for b in blocks:
    if not (LO <= b.start_offset <= HI):
        continue
    ins = list(b.instructions)
    r = analyzer.block_to_region.get(b)
    print('\n### @%d n=%d owner=%s' % (
        b.start_offset, len(ins),
        ('%s@%d' % (type(r).__name__, getattr(getattr(r, 'entry', None), 'start_offset', -1))) if r is not None else '-'))
    print('  succ=%s preds=%s' % (offs(getattr(b, 'successors', [])), offs(getattr(b, 'predecessors', []))))
    for i in ins:
        print('    @%-6d %-32s %s' % (i.offset, i.opname, i.argval))


def walk(rs, d=0):
    for r in rs:
        e = getattr(getattr(r, 'entry', None), 'start_offset', -1)
        print('  ' * d + '%s@%d hdr=%s cond=%s be=%s bes=%s cc=%s ccexpr=%s body=%s meta=%s' % (
            type(r).__name__, e,
            getattr(getattr(r, 'header_block', None), 'start_offset', None),
            getattr(getattr(r, 'condition_block', None), 'start_offset', None),
            getattr(getattr(r, 'back_edge_block', None), 'start_offset', None),
            offs(getattr(r, 'back_edge_blocks', None)),
            offs(getattr(r, 'condition_chain_blocks', None)),
            getattr(r, 'condition_chain_expr', None) is not None,
            offs(getattr(r, 'body_blocks', None)),
            {k: v for k, v in (getattr(r, 'metadata', None) or {}).items() if 'chain' in k or 'while' in k or 'bool' in k}))
        walk(getattr(r, 'children', None) or [], d + 1)


print('\n== regions ==')
walk(analyzer.regions)
