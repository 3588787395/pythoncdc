import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.dominator_analyzer import DominatorAnalyzer
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
        ra.analyze()
        
        # Check post-dominators
        b138 = cfg.get_block_by_offset(138)
        b180 = cfg.get_block_by_offset(180)
        print(f'Block@138 post_dominators: {[p.start_offset for p in getattr(b138, "post_dominators", [])]}')
        print(f'Block@180 post_dominators: {[p.start_offset for p in getattr(b180, "post_dominators", [])]}')
