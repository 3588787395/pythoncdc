import sys
sys.path.insert(0, '.')
from core.cfg.region_analyzer import RegionAnalyzer
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

# Check block at offset 284 (body_end=308 is the start of PUSH_EXC_INFO block 12)
# But normal_exit should be at offset 284 (block 21)
# Block 21: JUMP_FORWARD to 330 -> Block 16

for bid in sorted(cfg.blocks.keys()):
    block = cfg.blocks[bid]
    if block.start_offset == 284:
        print(f"Block {block.id} at 284 (normal-exit candidate):")
        for instr in block.instructions:
            print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argval}")
        last = block.get_last_instruction()
        print(f"  last instr: {last.opname} target={last.argval}")
        if last.opname == 'JUMP_FORWARD':
            target = cfg.get_block_by_offset(last.argval)
            print(f"  jump target: Block {target.id} at {target.start_offset}")
    
    if block.start_offset == 330:
        print(f"\nBlock {block.id} at 330 (exit block X candidate):")
        for instr in block.instructions:
            print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argval}")
