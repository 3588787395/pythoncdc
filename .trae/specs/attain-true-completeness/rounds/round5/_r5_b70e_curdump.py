# -*- coding: utf-8 -*-
"""R5 B70e evidence: CFG blocks + regions for g4b red units."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

out = open(os.path.join(HERE, '_r5_b70e_curdump.txt'), 'w', encoding='utf-8')


def w(s):
    out.write(s + '\n')


from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, WithRegion, LoopRegion, MatchRegion  # noqa: E402
import marshal  # noqa: E402


def load_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        data = f.read()
    return marshal.loads(data[16:])


code = load_code(r'test_repros\round5\rec1_synth_g4b_b70_whiletrue_with.pyc')

for target in [c for c in code.co_consts if hasattr(c, 'co_name')
               and c.co_name in ('g4b_wt_with_continue', 'g4b_wt_nested_with')]:
    w('#' * 30 + ' ' + target.co_name + ' ' + '#' * 30)
    builder = CFGBuilder()
    cfg = builder.build(target)
    w('=== CFG blocks ===')
    for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
        ins = [(i.offset, i.opname, i.argval) for i in b.instructions]
        w('BLK@%s..%s succ=%s pred=%s' % (
            b.start_offset,
            b.instructions[-1].offset if b.instructions else None,
            [s.start_offset for s in b.successors],
            [p.start_offset for p in b.predecessors]))
        for off, op, av in ins:
            w('   %s %s %s' % (off, op, av))
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    w('=== regions ===')
    for r in analyzer.regions:
        w('REGION %s entry=%s blocks=%s' % (
            type(r).__name__,
            getattr(r, 'entry', None) and r.entry.start_offset,
            [b.start_offset for b in getattr(r, 'blocks', [])]))
        cb = getattr(r, 'condition_block', None)
        if cb is not None:
            w('   cond=%s n=%s offs=%s' % (
                cb.start_offset, len(cb.instructions),
                [i.offset for i in cb.instructions]))
        if isinstance(r, IfRegion):
            w('   then=%s else=%s parent=%s' % (
                [b.start_offset for b in r.then_blocks],
                [b.start_offset for b in r.else_blocks],
                type(r.parent).__name__ if r.parent else None))
        if isinstance(r, WithRegion):
            w('   with_blocks=%s cleanup=%s body_off=[%s,%s] parent=%s' % (
                [b.start_offset for b in getattr(r, 'with_blocks', [])],
                [b.start_offset for b in getattr(r, 'cleanup_blocks', [])],
                getattr(r, 'body_offset_start', None),
                getattr(r, 'body_offset_end', None),
                type(r.parent).__name__ if r.parent else None))
        if isinstance(r, LoopRegion):
            w('   header=%s break_blocks=%s' % (
                getattr(r, 'header_block', None) and r.header_block.start_offset,
                [b.start_offset for b in getattr(r, 'break_blocks', [])]))
    w('=== block_to_region ===')
    for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
        r = analyzer.block_to_region.get(b)
        w('blk@%s -> %s' % (b.start_offset, type(r).__name__ if r else None))
out.close()
print('done')
