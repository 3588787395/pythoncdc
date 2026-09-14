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
        
        # Check back edges manually
        print('=== Block successors and back edges ===')
        for offset, block in sorted(cfg.blocks.items()):
            for succ in block.successors:
                is_back = dom.is_dominator(block, succ)
                last = block.get_last_instruction()
                last_op = last.opname if last else None
                print(f'  {offset} -> {succ.start_offset} is_dom={is_back} last_op={last_op}')
