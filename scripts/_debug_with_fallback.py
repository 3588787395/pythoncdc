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
ra = RegionAnalyzer(cfg, func)

block1 = cfg.blocks[1]
last_with = block1
with_entry_blocks = [block1]
block17 = cfg.blocks[17]
with_entry_blocks.append(block17)
body_start, body_end = ra._get_with_body_range(last_with)
with_body = ra._collect_with_body_blocks(last_with, body_start, body_end)

owned = set(with_entry_blocks) | set(with_body)
print(f"body_end = {body_end}")

# Scan with_body for normal-exit
for blk in with_body:
    last = blk.get_last_instruction()
    if last is None:
        continue
    if last.opname not in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
        continue
    if last.argval is None:
        continue
    target = cfg.get_block_by_offset(last.argval)
    if target is None or target in owned:
        print(f"  Block {blk.id} (offset {blk.start_offset}): {last.opname} -> Block {target.id if target else None}, but target in owned={target in owned if target else 'N/A'}")
        continue
    if target.start_offset <= body_end:
        print(f"  Block {blk.id} (offset {blk.start_offset}): {last.opname} -> Block {target.id} at {target.start_offset}, but target offset <= body_end ({body_end})")
        continue
    is_exit_handler = False
    for succ in blk.successors:
        if any(i.opname in ('WITH_EXCEPT_START', 'PUSH_EXC_INFO') for i in succ.instructions):
            is_exit_handler = True
            break
    print(f"  Block {blk.id} (offset {blk.start_offset}): {last.opname} -> Block {target.id} at {target.start_offset}, is_exit_handler={is_exit_handler}")
