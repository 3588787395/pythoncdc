# -*- coding: utf-8 -*-
"""R5 B70e: LoopRegion field dump for g4b red units."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

out = open(os.path.join(HERE, '_r5_b70e_loopfields.txt'), 'w', encoding='utf-8')


def w(s):
    out.write(s + '\n')


from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, WithRegion, IfRegion  # noqa: E402
import marshal  # noqa: E402


def load_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        data = f.read()
    return marshal.loads(data[16:])


code = load_code(r'test_repros\round5\rec1_synth_g4b_b70_whiletrue_with.pyc')

for target in [c for c in code.co_consts if hasattr(c, 'co_name')
               and c.co_name in ('g4b_wt_with_continue', 'g4b_wt_nested_with', 'g4b_while_cond_with')]:
    w('#' * 30 + ' ' + target.co_name + ' ' + '#' * 30)
    builder = CFGBuilder()
    cfg = builder.build(target)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    for r in analyzer.regions:
        if isinstance(r, LoopRegion):
            w('LoopRegion entry=%s header=%s' % (
                r.entry.start_offset,
                r.header_block and r.header_block.start_offset))
            w('  blocks=%s' % sorted(b.start_offset for b in r.blocks))
            w('  body_blocks=%s' % [b.start_offset for b in getattr(r, 'body_blocks', [])])
            w('  else_blocks=%s' % [b.start_offset for b in getattr(r, 'else_blocks', [])])
            w('  back_edge=%s break=%s cond=%s' % (
                getattr(r, 'back_edge_block', None) and r.back_edge_block.start_offset,
                [b.start_offset for b in getattr(r, 'break_blocks', [])],
                getattr(r, 'condition_block', None) and r.condition_block.start_offset))
            w('  init_blocks=%s' % [b.start_offset for b in getattr(r, 'init_blocks', [])])
            w('  metadata=%s' % dict(getattr(r, 'metadata', {}) or {}))
        if isinstance(r, WithRegion):
            w('WithRegion entry=%s parent=%s' % (
                r.entry.start_offset, type(r.parent).__name__ if r.parent else None))
            w('  blocks=%s' % sorted(b.start_offset for b in r.blocks))
            w('  with_blocks=%s' % [b.start_offset for b in r.with_blocks])
            w('  cleanup=%s' % [b.start_offset for b in r.cleanup_blocks])
            w('  exception=%s' % [b.start_offset for b in getattr(r, 'exception_blocks', [])])
            w('  body_off=[%s,%s] exit_block=%s exit_via_jump=%s' % (
                r.body_offset_start, r.body_offset_end,
                getattr(r, 'exit_block', None) and r.exit_block.start_offset,
                getattr(r, 'exit_via_jump', None)))
            w('  items=%s' % getattr(r, 'with_items', None))
        if isinstance(r, IfRegion):
            w('IfRegion entry=%s parent=%s' % (
                r.entry.start_offset, type(r.parent).__name__ if r.parent else None))
            w('  then=%s else=%s' % (
                [b.start_offset for b in r.then_blocks],
                [b.start_offset for b in r.else_blocks]))
out.close()
print('done')
