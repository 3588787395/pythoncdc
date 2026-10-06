import sys, marshal, dis
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, RegionType

f = open(r'F:\Downloads\pythoncdc-main\test_repros\round4\c4_02_loop_else.pyc', 'rb')
f.read(16)
code = marshal.load(f)

def find(co, name):
    for c in co.co_consts:
        if hasattr(c, 'co_name') and c.co_name == name:
            return c
    return None

cl = find(code, 'CL')
mm = find(cl, 'm')

builder = CFGBuilder()
cfg = builder.build(mm)
ra = RegionAnalyzer(cfg)
ra.analyze()
for r in ra.regions:
    _bl = getattr(r, 'blocks', None)
    if r.region_type in (RegionType.WHILE_LOOP, RegionType.FOR_LOOP):
        print('LOOP', r.region_type, 'entry', getattr(getattr(r, 'entry', None), 'start_offset', None))
        print('   blocks', sorted(b.start_offset for b in _bl) if _bl else _bl)
        print('   body_blocks', getattr(r, 'body_blocks', None) and sorted(b.start_offset for b in r.body_blocks))
        print('   else_blocks', getattr(r, 'else_blocks', None) and sorted(b.start_offset for b in r.else_blocks))
        print('   header', getattr(getattr(r, 'header_block', None), 'start_offset', None))
        print('   cond', getattr(getattr(r, 'condition_block', None), 'start_offset', None))
        print('   back_edge', getattr(getattr(r, 'back_edge_block', None), 'start_offset', None))
        print('   has_break', getattr(r, 'has_break', None))
        print('   break_blocks', getattr(r, 'break_blocks', None) and sorted(b.start_offset for b in r.break_blocks))
        print('   has_trailing_return_none', getattr(r, 'has_trailing_return_none', None))
        print('   else_is_follow', getattr(r, 'else_is_follow', None))
print('--- all blocks ---')
for b in sorted(cfg.blocks.values() if isinstance(cfg.blocks, dict) else cfg.blocks, key=lambda x: x.start_offset):
    print(b.start_offset, [i.opname for i in b.instructions][-3:], 'succ', sorted(s.start_offset for s in b.successors), 'exc', sorted(s.start_offset for s in b.exception_successors))