"""R23-N8 调试 multi_prod_to_dataframe 的区域识别"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, MatchRegion, IfRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# Find multi_prod_to_dataframe code object
import types
target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'multi_prod_to_dataframe':
        target = const
        break

if not target:
    print("Not found")
    sys.exit(1)

print(f"Found: {target.co_name}")

# Build CFG
builder = CFGBuilder()
cfg = builder.build(target)

# Analyze regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f"\n=== Regions (total {len(analyzer.regions)}) ===")
for region in sorted(analyzer.regions, key=lambda r: r.entry.start_offset if r.entry else 0):
    rtype = type(region).__name__
    entry_off = region.entry.start_offset if region.entry else None
    blocks_off = sorted(b.start_offset for b in region.blocks) if hasattr(region, 'blocks') else []
    print(f"  {rtype} entry={entry_off} blocks={blocks_off}")
    if isinstance(region, MatchRegion):
        print(f"    subject_block: {region.subject_block.start_offset if region.subject_block else None}")
        print(f"    case_blocks: {[b.start_offset for b in region.case_blocks]}")
        print(f"    case_patterns: {region.case_patterns}")
        print(f"    case_bodies: {[sorted(b.start_offset for b in body) for body in region.case_bodies]}")
        print(f"    merge_block: {region.merge_block.start_offset if region.merge_block else None}")
    if isinstance(region, IfRegion):
        print(f"    entry={entry_off} blocks={blocks_off}")

# Show block@152 instructions (the if k != 'fields' block)
print("\n=== Block@152 (if k != 'fields') ===")
for block in cfg.get_blocks_in_order():
    if block.start_offset == 152:
        print(f"  Block@{block.start_offset}:")
        for i in block.instructions:
            print(f"    {i.offset:>6} {i.opname:<25} {repr(i.argval)[:60]}")
        print(f"  successors: {[s.start_offset for s in block.successors]}")
        print(f"  predecessors: {[p.start_offset for p in block.predecessors]}")
        break

print("\n=== Block@304 (jump target) ===")
for block in cfg.get_blocks_in_order():
    if block.start_offset == 304:
        print(f"  Block@{block.start_offset}:")
        for i in block.instructions:
            print(f"    {i.offset:>6} {i.opname:<25} {repr(i.argval)[:60]}")
        print(f"  successors: {[s.start_offset for s in block.successors]}")
        break

# Test detection functions on block@152
print("\n=== Detection function results for block@152 ===")
b152 = None
for block in cfg.get_blocks_in_order():
    if block.start_offset == 152:
        b152 = block
        break
if b152:
    print(f"  _has_match_op: {analyzer._has_match_op(b152)}")
    print(f"  _is_case_pattern_block: {analyzer._is_case_pattern_block(b152)}")
    print(f"  _is_match_subject_block: {analyzer._is_match_subject_block(b152)}")
    print(f"  _is_simple_match_case_block: {analyzer._is_simple_match_case_block(b152)}")
    print(f"  _is_wildcard_match_block: {analyzer._is_wildcard_match_block(b152)}")
    print(f"  _is_none_match_block: {analyzer._is_none_match_block(b152)}")
    print(f"  block_to_region: {analyzer.block_to_region.get(b152)}")
