"""Debug repro_14 CFG and region analysis."""
import sys, marshal, types
sys.path.insert(0, '.')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

REPRO_DIR = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_46/test_engineer/minimal_repros"

with open(f'{REPRO_DIR}/repro_14_or_copy_store_simple.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func = None
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'func':
        func = const
        break

cfg = build_cfg(func)
print("=== CFG Blocks ===")
for b in cfg.get_blocks_in_order():
    last = b.get_last_instruction()
    last_str = f"{last.opname}" if last else "None"
    print(f"  Block {b.id} [{b.start_offset}-{b.end_offset}] last={last_str}")
    for instr in b.instructions:
        print(f"    {instr.offset:4d}  {instr.opname:30s}  {instr.arg if instr.arg is not None else ''}")

ra = RegionAnalyzer(cfg)
ra.analyze()

print(f"\n=== Regions ({len(ra.regions)}) ===")
for r in ra.regions:
    print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None}")
    if hasattr(r, 'blocks'):
        print(f"    blocks={[b.start_offset for b in r.blocks]}")
    if hasattr(r, 'then_blocks'):
        print(f"    then_blocks={[b.start_offset for b in r.then_blocks]}")
    if hasattr(r, 'else_blocks'):
        print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'merge_block') and r.merge_block:
        print(f"    merge_block={r.merge_block.start_offset}")
    if hasattr(r, 'op_chain') and r.op_chain:
        print(f"    op_chain={[(b.start_offset, op) for b, op in r.op_chain]}")
