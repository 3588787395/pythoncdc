import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.dominator_analyzer import LoopAnalyzer

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
        from core.cfg.dominator_analyzer import DominatorAnalyzer
        dom = DominatorAnalyzer(cfg)
        loop_analyzer = LoopAnalyzer(cfg, dom)
        all_loops = loop_analyzer.get_all_loops()
        print('=== All Loops ===')
        for header, sources in all_loops.items():
            print(f'  Header@{header.start_offset}: back_edges from {[s.start_offset for s, t in loop_analyzer.back_edges if t == header]}')
