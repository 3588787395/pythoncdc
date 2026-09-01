import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
import marshal, types

def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_func(code, name):
    if code.co_name == name:
        return code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            r = extract_func(c, name)
            if r: return r
    return None

code = load_code('site-packages/IQEngine/utils/scheduler.pyc')
func = extract_func(code, 'on_before_trading')
cfg = CFGBuilder().build(func)

for block_id in sorted(cfg.blocks.keys()):
    block = cfg.blocks[block_id]
    print(f'Block {block.id} (offset {block.start_offset}):')
    for instr in block.instructions:
        print(f'  {instr.offset:4d} {instr.opname:30s} {instr.argval}')
    print(f'  successors: {[s.id for s in block.successors]}')
    print(f'  predecessors: {[p.id for p in block.predecessors]}')
    print()
