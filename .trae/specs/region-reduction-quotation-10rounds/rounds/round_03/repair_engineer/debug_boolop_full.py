"""调试：完整 analyze 后检查 BoolOpRegion 是否被创建，以及 block 180 的归属变化。"""
import sys, os, py_compile, tempfile, types
sys.path.insert(0, '/workspace')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion

repro = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_03/test_engineer/minimal_repros/repro_03_long_or_chain_body_pass.py'
d = tempfile.mkdtemp()
pyc = os.path.join(d, 'r.pyc')
py_compile.compile(repro, pyc, doraise=True)
with open(pyc, 'rb') as f:
    f.read(16)
    code = __import__('marshal').load(f)

target = None
for c in code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == 'load_bars_from_hundsun':
        target = c
        break

cfg = build_cfg(target)
analyzer = RegionAnalyzer(cfg)

# Run Phase 1 + ChainedCompare (as before)
analyzer.dom_analyzer.analyze()
from core.cfg.dominator_analyzer import LoopAnalyzer
analyzer.loop_analyzer = LoopAnalyzer(cfg, analyzer.dom_analyzer)
analyzer.loop_analyzer.analyze()
analyzer._coalesce_nop_prefix_loop_headers()
analyzer.dominance_frontiers = analyzer.dom_analyzer.compute_all_dominance_frontiers()

try_regions = analyzer._identify_try_except_regions()
loop_regions = analyzer._identify_loop_regions()
with_regions = analyzer._identify_with_regions()
match_regions = analyzer._identify_match_regions()
assert_regions = analyzer._identify_assert_regions()
chained_compare_regions = analyzer._identify_chained_compare_regions(
    loop_regions=loop_regions, try_regions=try_regions,
    with_regions=with_regions, match_regions=match_regions,
    assert_regions=assert_regions)

# Now run BoolOp identification
existing = loop_regions + try_regions + with_regions + match_regions + assert_regions + chained_compare_regions
boolop_regions = analyzer._identify_boolop_regions(existing_regions=existing)
print(f"=== After _identify_boolop_regions: {len(boolop_regions)} BoolOpRegions created ===")
for i, br in enumerate(boolop_regions):
    chain = [(b.start_offset, op) for b, op in br.op_chain] if hasattr(br, 'op_chain') else 'N/A'
    blocks = sorted(b.start_offset for b in br.blocks) if br.blocks else []
    entry = br.entry.start_offset if br.entry else None
    print(f"  BoolOpRegion[{i}]: entry={entry} blocks={blocks}")
    print(f"    op_chain: {chain}")
    print(f"    merge_block: {br.merge_block.start_offset if hasattr(br, 'merge_block') and br.merge_block else None}")

blk180 = cfg.get_block_by_offset(180)
print(f"\n=== block 180 owner after BoolOp phase: {analyzer.block_to_region.get(blk180, 'NONE')} ===")

# Now run ternary + conditional
ternary_regions = analyzer._identify_ternary_regions(
    loop_regions=loop_regions, try_regions=try_regions,
    with_regions=with_regions, match_regions=match_regions,
    boolop_regions=boolop_regions, conditional_regions=chained_compare_regions)

conditional_regions = analyzer._identify_conditional_regions()
print(f"\n=== After _identify_conditional_regions: {len(conditional_regions)} ConditionalRegions ===")
for i, cr in enumerate(conditional_regions):
    entry = cr.entry.start_offset if cr.entry else None
    blocks = sorted(b.start_offset for b in cr.blocks) if cr.blocks else []
    rtype = cr.region_type
    print(f"  ConditionalRegion[{i}]: type={rtype} entry={entry} blocks={blocks}")

print(f"\n=== block 180 owner after Conditional phase: {analyzer.block_to_region.get(blk180, 'NONE')} ===")
print(f"=== block 202 owner after Conditional phase: {analyzer.block_to_region.get(cfg.get_block_by_offset(202), 'NONE')} ===")

# Check if BoolOpRegions still exist
print(f"\n=== BoolOpRegions still in analyzer.regions: {sum(1 for r in analyzer.regions if isinstance(r, BoolOpRegion))} ===")
for r in analyzer.regions:
    if isinstance(r, BoolOpRegion):
        chain = [(b.start_offset, op) for b, op in r.op_chain] if hasattr(r, 'op_chain') else 'N/A'
        print(f"  BoolOpRegion: entry={r.entry.start_offset if r.entry else None} op_chain={chain}")
