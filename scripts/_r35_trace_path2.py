#!/usr/bin/env python3
"""R35 诊断: trace which early-return path the module-level block takes."""
import sys, os, types, marshal, dis
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
pyc_path = PROJECT_ROOT / 'site-packages/IQCommon/util/strategy_info_utils.pyc'

# Load pyc
with open(pyc_path, 'rb') as f:
    f.read(16)
    code_obj = marshal.load(f)

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, RegionType, IfRegion, LoopRegion, WithRegion, TryExceptRegion, TernaryRegion, MatchRegion, BoolOpRegion, AssertRegion, BlockRole

cfg = build_cfg(code_obj, code_obj.co_name)
analyzer = RegionAnalyzer(cfg, code_obj)
regions = analyzer.analyze()

entry_block = cfg.entry_block
print(f"Entry block: offset={entry_block.start_offset}, instrs={len(entry_block.instructions)}")

# Check for UNPACK_SEQUENCE
has_unpack = any(i.opname in ('UNPACK_SEQUENCE', 'UNPACK_EX') for i in entry_block.instructions)
print(f"Has UNPACK: {has_unpack}")

# Check entry_region
entry_region = analyzer.get_entry_region_for_block(entry_block) or analyzer.get_region_for_block(entry_block)
print(f"Entry region (get_entry_region_for_block): {type(entry_region).__name__ if entry_region else None}")

_entry_region = analyzer.get_region_for_block(entry_block)
print(f"_entry_region (get_region_for_block): {type(_entry_region).__name__ if _entry_region else None}")

# Check block_role
block_role = analyzer.get_block_role(entry_block)
print(f"Block role: {block_role}")

# Check if it's in any region
for r in regions:
    if entry_block in r.blocks:
        print(f"  In region: {type(r).__name__}, entry={r.entry}, entry==entry_block: {r.entry is entry_block}")

# Check what _chain_instrs looks like
_chain_instrs = [i for i in entry_block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
print(f"\n_chain_instrs length: {len(_chain_instrs)}")
print(f"First 15 _chain_instrs:")
for i, instr in enumerate(_chain_instrs[:15]):
    print(f"  [{i:3d}] {instr.opname:35s} {repr(instr.argval)[:60]}")

# Check for STORE indices
store_indices = []
for ci, instr in enumerate(_chain_instrs):
    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
        store_indices.append(ci)
print(f"\nStore indices (first 10): {store_indices[:10]}")
print(f"Total stores: {len(store_indices)}")

# Check COPY before first store
if store_indices:
    first_store = store_indices[0]
    if first_store >= 1:
        prev = _chain_instrs[first_store - 1]
        print(f"Instruction before first STORE: {prev.opname} arg={prev.arg}")
    else:
        print("First STORE is at index 0 (no preceding instruction)")

# Check consecutive stores after first store
if store_indices:
    first = store_indices[0]
    consecutive = 0
    for idx in range(first, len(_chain_instrs)):
        if _chain_instrs[idx].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
            consecutive += 1
        else:
            break
    print(f"Consecutive stores after first: {consecutive}")
