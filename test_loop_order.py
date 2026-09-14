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
        # Manually simulate the loop creation
        
        all_loops = ra.loop_analyzer.get_all_loops()
        
        # Get dominance depth
        for header, sources in sorted(all_loops.items(), key=lambda x: ra._get_dominance_depth(x[0]), reverse=True):
            has_for_iter = any(i.opname in ('FOR_ITER', 'GET_ANEXT') for i in header.instructions)
            back_edge_sources = [src for src, tgt in ra.loop_analyzer.back_edges
                                if tgt == header and ra.dom_analyzer.is_dominator(header, src)]
            body = ra._collect_natural_loop_body(header, back_edge_sources, is_for_loop=has_for_iter)
            depth = ra._get_dominance_depth(header)
            print(f'header@{header.start_offset}: depth={depth}, body={[b.start_offset for b in body]}, back_edge_srcs={[s.start_offset for s in back_edge_sources]}')
