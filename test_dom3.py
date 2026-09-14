import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg

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
        
        # Check the block structure more carefully
        print('=== All blocks ===')
        for offset in sorted(cfg.blocks.keys()):
            block = cfg.blocks[offset]
            preds = [p.start_offset for p in block.predecessors]
            succs = [s.start_offset for s in block.successors]
            print(f'  Block@{offset}: preds={preds} succs={succs}')
            for instr in block.instructions:
                print(f'    {instr.offset}: {instr.opname} {instr.arg} ({instr.argval})')
        
        # Test if the dominance is computed at all
        from core.cfg.dominator_analyzer import DominatorAnalyzer
        dom = DominatorAnalyzer(cfg)
        print()
        print('=== Dominance tree ===')
        entry = cfg.entry_block
        print(f'Entry block: {entry.start_offset if entry else None}')
        # Try idom
        for offset in sorted(cfg.blocks.keys()):
            block = cfg.blocks[offset]
            idom = dom.get_immediate_dominator(block)
            print(f'  Block@{offset}: idom={idom.start_offset if idom else None}')
