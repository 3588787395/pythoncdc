import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

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
        
        # Check at the end of analyze
        for r in ra.regions:
            if isinstance(r, LoopRegion):
                print(f'Final LoopRegion: header={r.header_block.start_offset}, '
                      f'else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else None}, '
                      f'blocks={sorted([b.start_offset for b in r.blocks])}')
