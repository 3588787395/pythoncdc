import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.dominator_analyzer import DominatorAnalyzer, LoopAnalyzer
from core.cfg.region_analyzer import RegionAnalyzer

src = '''
def test_while_else_nested_break(data):
    while data:
        item = data[0]
        if item < 0:
            data.pop(0)
            continue
        if item == 0:
            break
        data.pop(0)
    else:
        data.append(-1)
    return data
'''

code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_code'):
        cfg = build_cfg(c)
        ra = RegionAnalyzer(cfg)
        regions = ra.analyze()
        
        da = ra.dom_analyzer
        la = ra.loop_analyzer
        
        if la:
            print('back_edges:', [(s.start_offset, t.start_offset) for s, t in la.back_edges])
            print('loop_headers:', [h.start_offset for h in la.loop_headers])
        
        from core.cfg.region_analyzer import LoopRegion
        for r in regions:
            if isinstance(r, LoopRegion):
                print(f'LoopRegion: header={r.header_block.start_offset if r.header_block else None}')
                print(f'  condition_block={r.condition_block.start_offset if r.condition_block else None}')
                print(f'  body_blocks={[b.start_offset for b in r.body_blocks]}')
                print(f'  else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else None}')
                print(f'  break_blocks={[b.start_offset for b in r.break_blocks] if r.break_blocks else []}')
                print(f'  has_break={r.has_break}')
