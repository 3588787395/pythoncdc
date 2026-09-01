"""R25: Debug BoolOpRegion detection for share_change"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion, RegionType

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# Find share_change code object
import types
target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'share_change':
        target = const
        break

print(f"=== share_change analysis ===")
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f"\n=== Blocks around the compound conditions ===")
for offset in [114, 118, 122, 134, 138, 142, 154, 158, 162, 182]:
    blk = cfg.get_block_by_offset(offset)
    if blk is None:
        print(f"  offset {offset}: NOT FOUND")
        continue
    last = blk.get_last_instruction()
    region = analyzer.block_to_region.get(blk)
    region_type = type(region).__name__ if region else "None"
    argval_str = repr(last.argval) if last else ''
    print(f"  offset {offset}: last={last.opname if last else None}({argval_str}) region={region_type}")

print(f"\n=== All BoolOpRegions ===")
for r in analyzer.regions:
    if isinstance(r, BoolOpRegion):
        entry_off = r.entry.start_offset
        chain_offsets = [(b.start_offset, op) for b, op in r.op_chain]
        merge_off = r.merge_block.start_offset if r.merge_block else None
        print(f"  BoolOpRegion: entry={entry_off} chain={chain_offsets} merge={merge_off}")

print(f"\n=== All IfRegions (first 20) ===")
count = 0
for r in analyzer.regions:
    if isinstance(r, IfRegion):
        entry_off = r.entry.start_offset
        merge_off = r.merge_block.start_offset if r.merge_block else None
        print(f"  IfRegion: entry={entry_off} merge={merge_off}")
        count += 1
        if count >= 20:
            break
