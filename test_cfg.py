import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg

src = "def f(direction): x = f\"{'IN' if direction == '0' else 'OUT'}END\"; return x"
code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_code'):
        cfg = build_cfg(c)
        print('Blocks:')
        for offset, block in sorted(cfg.blocks.items()):
            print(f'  Block@{offset}:')
            for instr in block.instructions:
                print(f'    {instr.offset}: {instr.opname} {instr.arg} {instr.argval}')
            print(f'    successors: {[s.start_offset for s in block.successors]}')
