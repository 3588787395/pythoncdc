# -*- coding: utf-8 -*-
"""R5 B70e-a veto evidence: post-fix WithRegion/IfRegion/LoopRegion fields for g4b units."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

out = open(os.path.join(HERE, '_r5_b70e_veto_out.txt'), 'w', encoding='utf-8')


def w(s):
    out.write(s + '\n')


from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, WithRegion, LoopRegion  # noqa: E402
import marshal  # noqa: E402


def load_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        data = f.read()
    return marshal.loads(data[16:])


for pyc, names in [
    (r'test_repros\round5\rec1_synth_g4b_b70_whiletrue_with.pyc',
     ('g4b_wt_with_continue', 'g4b_wt_nested_with', 'g4b_while_cond_with', 'g4b_wt_with_noas')),
    (r'test_repros\round5\rec1_synth_g4a_b70_whiletrue_with.pyc', None),
]:
    code = load_code(pyc)
    consts = [c for c in code.co_consts if hasattr(c, 'co_name')]
    if names is not None:
        consts = [c for c in consts if c.co_name in names]
    for target in consts:
        w('#' * 30 + ' ' + target.co_name + ' ' + '#' * 30)
        builder = CFGBuilder()
        cfg = builder.build(target)
        analyzer = RegionAnalyzer(cfg)
        analyzer.analyze()
        for r in analyzer.regions:
            if isinstance(r, WithRegion):
                w('WithRegion entry=%s parent=%s' % (
                    r.entry and r.entry.start_offset,
                    type(r.parent).__name__ if r.parent else None))
                w('  with_blocks=%s' % [b.start_offset for b in getattr(r, 'with_blocks', [])])
                w('  cleanup=%s exception=%s' % (
                    [b.start_offset for b in getattr(r, 'cleanup_blocks', [])],
                    [b.start_offset for b in getattr(r, 'exception_blocks', [])]))
                w('  body_off=[%s,%s] exit_block=%s exit_via_jump=%s' % (
                    getattr(r, 'body_offset_start', None), getattr(r, 'body_offset_end', None),
                    getattr(r, 'exit_block', None) and r.exit_block.start_offset,
                    getattr(r, 'exit_via_jump', None)))
            if isinstance(r, IfRegion):
                w('IfRegion entry=%s then=%s else=%s' % (
                    r.entry and r.entry.start_offset,
                    [b.start_offset for b in r.then_blocks],
                    [b.start_offset for b in r.else_blocks]))
            if isinstance(r, LoopRegion):
                w('LoopRegion entry=%s back_edge=%s break=%s' % (
                    r.entry and r.entry.start_offset,
                    getattr(r, 'back_edge_block', None) and r.back_edge_block.start_offset,
                    [b.start_offset for b in getattr(r, 'break_blocks', [])]))
out.close()
print('done')
