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

# Simulate _find_with_exit_block for the outer with
# with_entry_blocks include block 1 (BEFORE_WITH at offset 50)
# after_bw_block = block 17 (POP_TOP at offset 52)

# body_start, body_end
block1 = cfg.blocks[1]
last_with = block1
# Find body range
for entry in cfg.exception_table:
    # Find the entry that covers BEFORE_WITH
    bw_offset = None
    for instr in block1.instructions:
        if instr.opname == 'BEFORE_WITH':
            bw_offset = instr.offset
            break
    if bw_offset is not None and entry.get('start', 0) <= bw_offset < entry.get('end', 9999):
        print(f"Exception entry: start={entry.get('start')}, end={entry.get('end')}, target={entry.get('target')}, depth={entry.get('depth')}")

# Now call the real method
with_entry_blocks = [block1]
# Block 17 is after BEFORE_WITH (POP_TOP)
block17 = cfg.blocks[17]
after_bw = block17
if after_bw and after_bw not in with_entry_blocks:
    with_entry_blocks.append(after_bw)

body_start, body_end = ra._get_with_body_range(last_with)
print(f"body_start={body_start}, body_end={body_end}")

with_body = ra._collect_with_body_blocks(last_with, body_start, body_end)
print(f"with_body blocks: {sorted([b.id for b in with_body])}")

exception_blocks, cleanup_blocks = ra._collect_with_cleanup_blocks(with_entry_blocks, with_body, body_start, body_end)
print(f"exception_blocks: {sorted([b.id for b in exception_blocks])}")
print(f"cleanup_blocks: {sorted([b.id for b in cleanup_blocks])}")

exit_block, via_jump = ra._find_with_exit_block(with_entry_blocks, with_body, body_start, body_end)
print(f"exit_block: {exit_block.id if exit_block else None}, via_jump={via_jump}")
