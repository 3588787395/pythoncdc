import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

src = '''def f(x, limit):
    while x < limit:
        if x < 0:
            continue
        a = x * 2
        x += 1'''

code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_code'):
        cfg = build_cfg(c)
        ra = RegionAnalyzer(cfg)
        regions = ra.analyze()
        
        for r in regions:
            if isinstance(r, LoopRegion):
                print(f'LoopRegion: header={r.header_block.start_offset}')
                print(f'  condition_block={r.condition_block.start_offset if r.condition_block else None}')
                print(f'  body_blocks={sorted([b.start_offset for b in r.body_blocks])}')
                print(f'  else_blocks={sorted([b.start_offset for b in r.else_blocks]) if r.else_blocks else None}')
                print(f'  break_blocks={sorted([b.start_offset for b in r.break_blocks]) if r.break_blocks else []}')
                print(f'  has_break={r.has_break}')
                print(f'  is_while_true={r.is_while_true}')
                print()
