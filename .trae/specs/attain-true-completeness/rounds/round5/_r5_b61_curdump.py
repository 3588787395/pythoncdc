# -*- coding: utf-8 -*-
"""R5 B61 current-state dump: CFG blocks + regions for r8_dh_match_multi."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

out = open(os.path.join(HERE, '_r5_b61_curdump.txt'), 'w', encoding='utf-8')


def w(s):
    out.write(s + '\n')


from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, AssertRegion, MatchRegion  # noqa: E402
import marshal  # noqa: E402


def load_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        data = f.read()
    return marshal.loads(data[16:])


code = load_code(r'test_repros\round8\r8_09_deep_host_combo.pyc')
target = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'r8_dh_match_multi':
        target = c
        break
w('co_name=%s' % target.co_name)

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
if hasattr(analyzer, 'setup'):
    pass
analyzer.analyze()
w('=== regions ===')
for r in analyzer.regions:
    w('REGION %s entry=%s blocks=%s' % (
        type(r).__name__,
        getattr(r, 'entry', None) and r.entry.start_offset,
        [b.start_offset for b in getattr(r, 'blocks', [])]))
    cb = getattr(r, 'condition_block', None)
    if cb is not None:
        w('   cond=%s n=%s offs=%s is_real_cfg=%s' % (
            cb.start_offset, len(cb.instructions),
            [i.offset for i in cb.instructions],
            cb in set(cfg.blocks)))
    if isinstance(r, IfRegion):
        w('   then=%s else=%s parent=%s' % (
            [b.start_offset for b in r.then_blocks],
            [b.start_offset for b in r.else_blocks],
            type(r.parent).__name__ if r.parent else None))
    if isinstance(r, AssertRegion):
        w('   cond_blk=%s msg=%s' % (
            r.condition_block.start_offset if r.condition_block else None,
            r.message_block.start_offset if getattr(r, 'message_block', None) else None))
    if isinstance(r, MatchRegion):
        w('   case_blocks=%s bodies=%s guards=%s' % (
            [b.start_offset for b in r.case_blocks],
            [[b.start_offset for b in body] for body in r.case_bodies],
            r.case_guards))
        w('   body_start_indices=%s' % getattr(r, 'case_body_start_indices', None))
w('=== block_to_region (30/60/68/74) ===')
for off in (30, 60, 68, 74):
    blk = cfg.get_block_by_offset(off)
    r = analyzer.block_to_region.get(blk)
    w('blk@%s -> %s' % (off, type(r).__name__ if r else None))
out.close()
print('done')
