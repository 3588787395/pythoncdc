"""Debug why block 84 is not detected as finally_copy."""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')

import marshal
import types

with open('.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_11/test_engineer/minimal_repros/repro_r11_06_try_except_finally_continue.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

builder = CFGBuilder()
cfg = builder.build(code)

analyzer = RegionAnalyzer(cfg)
handler_infos = analyzer._parse_exception_table()

# Check the finally handler
finally_info = handler_infos[1]  # type=finally
print(f"Finally handler: try=[{finally_info['try_start']},{finally_info['try_end']}), handler_start={finally_info['handler_start']}")

# Check paired_except_infos
paired_except_infos = []
for info in handler_infos:
    if info is finally_info:
        continue
    if info['try_start'] == finally_info['try_start'] and info['handler_type'] == 'except':
        paired_except_infos.append(info)
        print(f"Paired except: try=[{info['try_start']},{info['try_end']}), handler_start={info['handler_start']}")

# Simulate _collect_handler_chain for the paired except
all_except_handlers = []
all_handler_entry_blocks = []
all_handler_blocks_set = set()

for except_info in paired_except_infos:
    handler_body = analyzer._collect_handler_chain(
        except_info['handler_start'], all_except_handlers,
        all_handler_entry_blocks, all_handler_blocks_set)
    print(f"\nExcept handler body blocks: {[b.start_offset for b in handler_body]}")
    for b in handler_body:
        last = b.instructions[-1] if b.instructions else None
        print(f"  block@{b.start_offset}: last={last.opname if last else 'None'}, succs={[s.start_offset for s in b.successors]}")

print(f"\nall_except_handlers: {[(t, n, [b.start_offset for b in body]) for t, n, body in all_except_handlers]}")
print(f"all_handler_blocks_set: {[b.start_offset for b in all_handler_blocks_set]}")

# Now check what _collect_finally_body_blocks returns
try_blocks = []
# Get try blocks for the finally handler
for blk in cfg.get_blocks_in_order():
    if any(finally_info['try_start'] <= instr.offset < finally_info['try_end'] for instr in blk.instructions):
        if blk not in all_handler_blocks_set:
            try_blocks.append(blk)

print(f"\ntry_blocks: {[b.start_offset for b in try_blocks]}")

handler_entry_block = cfg.get_block_by_offset(finally_info['handler_start'])
body_blocks, copy_blocks = analyzer._collect_finally_body_blocks(
    handler_entry_block, try_blocks, all_except_handlers)

print(f"\nbody_blocks (finally): {[b.start_offset for b in body_blocks]}")
print(f"copy_blocks: {copy_blocks}")

# Check if block 84 is a successor of any handler body block
print("\nChecking handler body block successors:")
for t, n, body in all_except_handlers:
    for b in body:
        for succ in b.successors:
            print(f"  block@{b.start_offset} -> succ@{succ.start_offset}")
            if succ.start_offset == 84:
                print(f"    *** FOUND block 84 as successor of handler body block {b.start_offset}!")
