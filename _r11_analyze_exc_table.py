"""Analyze repro_r11_06 exception table and handler classification."""
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

print("Exception table:")
for entry in cfg.exception_table:
    start = entry.get('start', 0)
    end = entry.get('end', 0)
    target = entry.get('target', 0)
    depth = entry.get('depth', 0)
    lasti = entry.get('lasti', False)
    target_block = cfg.get_block_by_offset(target)
    target_first_instr = target_block.instructions[0].opname if target_block and target_block.instructions else 'None'
    print(f"  [{start:3d} to {end:3d}] -> {target:3d} (depth={depth}, lasti={lasti}), target_first={target_first_instr}")

# Check what blocks are in try range
print("\nBlock analysis:")
for blk in cfg.get_blocks_in_order():
    in_any_try = False
    for entry in cfg.exception_table:
        start = entry.get('start', 0)
        end = entry.get('end', 0)
        if any(start <= instr.offset < end for instr in blk.instructions):
            in_any_try = True
            break
    is_handler = blk.instructions[0].opname in ('PUSH_EXC_INFO', 'COPY') if blk.instructions else False
    print(f"  blk@{blk.start_offset}: in_try={in_any_try}, is_handler={is_handler}, last={blk.instructions[-1].opname if blk.instructions else 'None'}")
