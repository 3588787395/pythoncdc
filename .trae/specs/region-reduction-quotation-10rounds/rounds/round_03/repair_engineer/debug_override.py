"""调试：完整 analyze 后检查 BoolOpRegion 是否被 Conditional 覆盖。"""
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
analyzer.analyze()

blk180 = cfg.get_block_by_offset(180)
blk202 = cfg.get_block_by_offset(202)
blk262 = cfg.get_block_by_offset(262)
blk396 = cfg.get_block_by_offset(396)
blk274 = cfg.get_block_by_offset(274)

print("=== After full analyze() ===")
for blk in [blk180, blk202, blk262, blk396, blk274]:
    owner = analyzer.block_to_region.get(blk)
    print(f"  block@{blk.start_offset}: owner={owner.region_type if owner else 'NONE'}")

print(f"\n=== All regions ===")
for r in analyzer.regions:
    entry = r.entry.start_offset if r.entry else None
    blocks = sorted(b.start_offset for b in r.blocks) if r.blocks else []
    print(f"  {r.region_type}: entry={entry} blocks={blocks}")
    if isinstance(r, BoolOpRegion):
        chain = [(b.start_offset, op) for b, op in r.op_chain]
        print(f"    op_chain: {chain}")
        print(f"    merge_block: {r.merge_block.start_offset if r.merge_block else None}")

# Check if BoolOpRegion for block 180 exists
boolop_for_180 = [r for r in analyzer.regions if isinstance(r, BoolOpRegion) and blk180 in r.blocks]
print(f"\n=== BoolOpRegion containing block 180: {len(boolop_for_180)} ===")
for r in boolop_for_180:
    print(f"  entry={r.entry.start_offset} blocks={sorted(b.start_offset for b in r.blocks)}")

# Check the IfRegion/IF_ELIF_CHAIN that owns block 180
if_region_for_180 = [r for r in analyzer.regions if isinstance(r, IfRegion) and blk180 in r.blocks]
print(f"\n=== IfRegion containing block 180: {len(if_region_for_180)} ===")
for r in if_region_for_180:
    entry = r.entry.start_offset if r.entry else None
    blocks = sorted(b.start_offset for b in r.blocks) if r.blocks else []
    cond = r.condition_block.start_offset if r.condition_block else None
    then_blocks = sorted(b.start_offset for b in r.then_blocks) if hasattr(r, 'then_blocks') and r.then_blocks else []
    else_blocks = sorted(b.start_offset for b in r.else_blocks) if hasattr(r, 'else_blocks') and r.else_blocks else []
    print(f"  type={r.region_type} entry={entry} cond={cond} blocks={blocks}")
    print(f"    then={then_blocks} else={else_blocks}")
