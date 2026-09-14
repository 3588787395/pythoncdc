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
        
        # Get loop bodies from the LoopAnalyzer
        la = ra.loop_analyzer
        
        # For inner loop (header=6), manually compute loop_successors
        h6 = cfg.get_block_by_offset(6)
        body_6 = la.loop_bodies.get(h6, set())
        body_set_6 = body_6 | {h6}
        
        print('=== Inner loop (header=6) ===')
        print(f'body_set_6: {[b.start_offset for b in body_set_6]}')
        
        # loop_successors computation (line 4798-4831)
        # header successors not in body
        header_succs = [s for s in h6.successors if s not in body_set_6 and s != h6]
        print(f'header successors not in body: {[s.start_offset for s in header_succs]}')
        
        # body block successors not in body
        body_succs = []
        for block in body_set_6:
            if block == h6:
                continue
            for succ in block.successors:
                if succ not in body_set_6 and succ != h6 and succ not in header_succs:
                    body_succs.append((block.start_offset, succ.start_offset))
        print(f'body successors not in body: {body_succs}')
        
        # Now for the outer loop (header=2)
        h2 = cfg.get_block_by_offset(2)
        body_2 = la.loop_bodies.get(h2, set())
        body_set_2 = body_2 | {h2}
        
        print()
        print('=== Outer loop (header=2) ===')
        print(f'body_set_2: {[b.start_offset for b in body_set_2]}')
        
        header_succs_2 = [s for s in h2.successors if s not in body_set_2 and s != h2]
        print(f'header successors not in body: {[s.start_offset for s in header_succs_2]}')
