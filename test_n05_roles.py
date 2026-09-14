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
        
        # Check block roles
        print('Block roles:', {k: v for k, v in ra.block_roles.items()})
        
        # Check what blocks are in the loop region
        for r in regions:
            if isinstance(r, LoopRegion):
                print(f'LoopRegion blocks: {sorted([b.start_offset for b in r.blocks])}')
                print(f'LoopRegion body_blocks: {sorted([b.start_offset for b in r.body_blocks])}')
