#!/usr/bin/env python3
"""R35 诊断: trace which code path module-level entry block takes."""
import sys, os
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ['R35_DEBUG_MODULE'] = '1'

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
pyc_path = PROJECT_ROOT / 'site-packages/IQCommon/util/strategy_info_utils.pyc'

from core.pyc_loader_v2 import load_pyc_file
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, WithRegion, TryExceptRegion, TernaryRegion, MatchRegion, BoolOpRegion, AssertRegion, RegionType

code_obj = load_pyc_file(str(pyc_path))
cfg = build_cfg(code_obj, pyc_path.name)
analyzer = RegionAnalyzer(cfg, code_obj)
regions = analyzer.analyze()

entry_block = cfg.entry_block
print(f"Entry block: offset={entry_block.start_offset}, instrs={len(entry_block.instructions)}")
print(f"Regions: {len(regions)}")

entry_region = analyzer.get_entry_region_for_block(entry_block) or analyzer.get_region_for_block(entry_block)
print(f"Entry region: {type(entry_region).__name__ if entry_region else None}")

if entry_region:
    print(f"  region type: {entry_region.region_type}")
    print(f"  region entry: {entry_region.entry}")
    print(f"  entry is entry_block: {entry_region.entry is entry_block}")

# Check what _entry_region would be (second lookup)
_entry_region = analyzer.get_region_for_block(entry_block)
print(f"_entry_region (get_region_for_block): {type(_entry_region).__name__ if _entry_region else None}")

# Check all regions containing entry_block
containing = [r for r in regions if entry_block in r.blocks]
print(f"Regions containing entry_block: {len(containing)}")
for r in containing:
    print(f"  {type(r).__name__}: entry={r.entry}, type={r.region_type}")

# Print the first 20 instructions of entry_block
print("\n=== First 30 instructions of entry_block ===")
for i, instr in enumerate(entry_block.instructions[:30]):
    print(f"  [{i:3d}] {instr.opname:35s} {repr(instr.argval)[:60]}")

# Check if entry_block has block_role
block_role = analyzer.get_block_role(entry_block)
print(f"\nBlock role: {block_role}")

# Check successors
print(f"Successors: {[s.start_offset for s in entry_block.successors]}")
print(f"Predecessors: {[s.start_offset for s in entry_block.predecessors]}")
