import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, TryExceptRegion, LoopRegion

src = '''
def test():
    try:
        x = 1
    except BaseException:
        while x != 0:
            try:
                x = x - 1
            except BaseException:
                x = 0
        else:
            if x == 0:
                return None
    else:
        if x > 0:
            try:
                return x
            except BaseException:
                return None
        else:
            return -1
'''

code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test':
        target = c
        break

# Build CFG
cfg = build_cfg(target, '<test>')

# Analyze regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find the while loop
for r in analyzer.regions:
    if isinstance(r, LoopRegion):
        cond = r.condition_block
        print(f"LoopRegion: cond_block offset={getattr(cond, 'start_offset', None)}")
        if cond:
            print(f"  cond_block instructions:")
            for i in cond.instructions:
                print(f"    {i.offset}: {i.opname} {getattr(i, 'argval', '')}")
            print(f"  cond_block predecessors:")
            for p in cond.predecessors:
                print(f"    offset={p.start_offset}")
                for i in p.instructions:
                    print(f"      {i.offset}: {i.opname} {getattr(i, 'argval', '')}")
