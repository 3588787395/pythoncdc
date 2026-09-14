import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg

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
        print('=== All blocks ===')
        for offset in sorted(cfg.blocks.keys()):
            block = cfg.blocks[offset]
            preds = [p.start_offset for p in block.predecessors]
            succs = [s.start_offset for s in block.successors]
            print(f'  Block@{offset}: preds={preds} succs={succs}')
            for instr in block.instructions:
                print(f'    {instr.offset}: {instr.opname} {instr.arg} ({instr.argval})')
