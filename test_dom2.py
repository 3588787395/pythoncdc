import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.dominator_analyzer import DominatorAnalyzer

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
        dom = DominatorAnalyzer(cfg)
        
        # Test dominance relationships
        b2 = cfg.get_block_by_offset(2)
        b4 = cfg.get_block_by_offset(34)
        b6 = cfg.get_block_by_offset(6)
        b7 = cfg.get_block_by_offset(92)
        
        print(f'Block@4 dominates Block@2? {dom.is_dominator(b4, b2)}')
        print(f'Block@7 dominates Block@6? {dom.is_dominator(b7, b6)}')
        print(f'Block@2 dominates Block@4? {dom.is_dominator(b2, b4)}')
        print(f'Block@2 dominates Block@7? {dom.is_dominator(b2, b7)}')
        print(f'Block@6 dominates Block@4? {dom.is_dominator(b6, b4)}')
        print(f'Block@6 dominates Block@7? {dom.is_dominator(b6, b7)}')
        
        # The loop analyzer requires header dominates back-edge source
        # Block@4 -> Block@2: need Block@2 to dominate Block@4 (it does)
        # But also need Block@4 to be a back-edge to Block@2
        # Actually the check is: is_dominator(header, src) meaning header dominates src
        print()
        print(f'Block@2 dominates Block@4? {dom.is_dominator(b2, b4)}')
        print(f'Block@2 dominates Block@7? {dom.is_dominator(b2, b7)}')
        print(f'Block@6 dominates Block@4? {dom.is_dominator(b6, b4)}')
        print(f'Block@6 dominates Block@7? {dom.is_dominator(b6, b7)}')
