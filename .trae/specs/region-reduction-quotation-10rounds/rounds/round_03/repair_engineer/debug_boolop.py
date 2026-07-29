"""调试：直接测试 _detect_boolop_conditional_chain 从 block 180 开始。"""
import sys, os, py_compile, tempfile, types, dis
sys.path.insert(0, '/workspace')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

repro = '/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_03/test_engineer/minimal_repros/repro_03_long_or_chain_body_pass.py'
d = tempfile.mkdtemp()
pyc = os.path.join(d, 'r.pyc')
py_compile.compile(repro, pyc, doraise=True)
with open(pyc, 'rb') as f:
    f.read(16)
    code = __import__('marshal').load(f)

# find load_bars_from_hundsun
for c in code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == 'load_bars_from_hundsun':
        target = c
        break

cfg = build_cfg(target)
analyzer = RegionAnalyzer(cfg)
# Run full analyze to get all regions
analyzer.analyze()

# Now find block 180
blk180 = cfg.get_block_by_offset(180)
blk202 = cfg.get_block_by_offset(202)

print("=== block 180 info ===")
print(f"  last instr: {blk180.get_last_instruction().opname} {blk180.get_last_instruction().argval}")
print(f"  in block_to_region: {blk180 in analyzer.block_to_region}")
if blk180 in analyzer.block_to_region:
    print(f"  owner: {analyzer.block_to_region[blk180].region_type}")

print("\n=== block 202 info ===")
print(f"  last instr: {blk202.get_last_instruction().opname} {blk202.get_last_instruction().argval}")
print(f"  in block_to_region: {blk202 in analyzer.block_to_region}")
if blk202 in analyzer.block_to_region:
    print(f"  owner: {analyzer.block_to_region[blk202].region_type}")

# Test chain detection from block 180
print("\n=== _detect_boolop_conditional_chain from block 180 ===")
# Build claimed set as boolop would see it
claimed = set()
for blk, reg in analyzer.block_to_region.items():
    claimed.add(blk)
print(f"  claimed blocks: {sorted(b.start_offset for b in claimed)}")
print(f"  block 180 in claimed: {blk180 in claimed}")

chain = analyzer._detect_boolop_conditional_chain(blk180, claimed, skip_claimed_check=False)
print(f"  chain from 180: {[(b.start_offset, op) for b, op in chain] if chain else None}")

chain2 = analyzer._detect_boolop_conditional_chain(blk202, claimed, skip_claimed_check=False)
print(f"  chain from 202: {[(b.start_offset, op) for b, op in chain2] if chain2 else None}")

# Also test _detect_boolop_chain_start
print("\n=== _detect_boolop_chain_start ===")
chain3 = analyzer._detect_boolop_chain_start(blk180, claimed)
print(f"  chain_start from 180: {[(b.start_offset, op) for b, op in chain3] if chain3 else None}")
chain4 = analyzer._detect_boolop_chain_start(blk202, claimed)
print(f"  chain_start from 202: {[(b.start_offset, op) for b, op in chain4] if chain4 else None}")

# Check _is_valid_2elem_mixed_chain
print("\n=== _is_valid_2elem_mixed_chain ===")
if chain3:
    print(f"  is_valid_2elem_mixed(chain_start from 180): {analyzer._is_valid_2elem_mixed_chain(chain3)}")
