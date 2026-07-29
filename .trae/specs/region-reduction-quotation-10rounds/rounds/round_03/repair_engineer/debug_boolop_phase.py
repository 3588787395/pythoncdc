"""调试：模拟 BoolOp 识别阶段的 claimed 集合，测试 block 180 的链检测。

复现 load_bars_from_hundsun 中 `is_utc == '0' and (typet==1 or ... or typet==13)`
长 or 链的 BoolOp 识别失败根因。
"""
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

target = None
for c in code.co_consts:
    if isinstance(c, types.CodeType) and c.co_name == 'load_bars_from_hundsun':
        target = c
        break

cfg = build_cfg(target)
analyzer = RegionAnalyzer(cfg)

# Replicate analyze() up to BoolOp phase
analyzer.dom_analyzer.analyze()
from core.cfg.dominator_analyzer import LoopAnalyzer
analyzer.loop_analyzer = LoopAnalyzer(cfg, analyzer.dom_analyzer)
analyzer.loop_analyzer.analyze()
analyzer._coalesce_nop_prefix_loop_headers()
analyzer.dominance_frontiers = analyzer.dom_analyzer.compute_all_dominance_frontiers()

# Phase 1
try_regions = analyzer._identify_try_except_regions()
loop_regions = analyzer._identify_loop_regions()
with_regions = analyzer._identify_with_regions()
match_regions = analyzer._identify_match_regions()
assert_regions = analyzer._identify_assert_regions()

# Phase 2 pre-boolop
chained_compare_regions = analyzer._identify_chained_compare_regions(
    loop_regions=loop_regions, try_regions=try_regions,
    with_regions=with_regions, match_regions=match_regions,
    assert_regions=assert_regions)

# Build claimed set as _identify_boolop_regions would
claimed = set(analyzer.block_to_region.keys())
existing = loop_regions + try_regions + with_regions + match_regions + assert_regions + chained_compare_regions
for region in existing:
    claimed.update(region.blocks)

print(f"=== BoolOp-phase claimed blocks: {sorted(b.start_offset for b in claimed)}")

# Find the 'and' block (is_utc == '0') and the first 'or' block
# From debug, block 180 = is_utc check (POP_JUMP_FORWARD_IF_FALSE), block 202 = first or
# But offsets may differ in repro. Let's scan for the pattern.
and_blk = None
or_blk = None
for blk in cfg.get_blocks_in_order():
    last = blk.get_last_instruction()
    if not last:
        continue
    # 'and' pattern: POP_JUMP_FORWARD_IF_FALSE jumping to a far exit (the else)
    # 'or' pattern: POP_JUMP_FORWARD_IF_TRUE jumping to the then-body
    if last.opname == 'POP_JUMP_FORWARD_IF_TRUE':
        if or_blk is None:
            or_blk = blk
    if last.opname == 'POP_JUMP_FORWARD_IF_FALSE' and and_blk is None:
        # Check if this block's fallthrough leads to an or-chain
        ft = [s for s in blk.successors]
        for s in ft:
            sl = s.get_last_instruction()
            if sl and sl.opname == 'POP_JUMP_FORWARD_IF_TRUE':
                and_blk = blk
                break

print(f"\nand_blk (is_utc=='0'): offset={and_blk.start_offset if and_blk else None}")
print(f"or_blk (first or): offset={or_blk.start_offset if or_blk else None}")

if and_blk:
    al = and_blk.get_last_instruction()
    print(f"  and_blk last: {al.opname} {al.argval}")
    print(f"  and_blk in claimed: {and_blk in claimed}")
    print(f"  and_blk successors: {[s.start_offset for s in and_blk.successors]}")

if or_blk:
    ol = or_blk.get_last_instruction()
    print(f"  or_blk last: {ol.opname} {ol.argval}")

# Test chain detection from and_blk with BoolOp-phase claimed set
if and_blk:
    print("\n=== _detect_boolop_conditional_chain from and_blk (BoolOp-phase claimed) ===")
    chain = analyzer._detect_boolop_conditional_chain(and_blk, claimed, skip_claimed_check=False)
    print(f"  chain: {[(b.start_offset, op) for b, op in chain] if chain else None}")

    print("\n=== _detect_boolop_chain_start from and_blk (BoolOp-phase claimed) ===")
    chain2 = analyzer._detect_boolop_chain_start(and_blk, claimed)
    print(f"  chain_start: {[(b.start_offset, op) for b, op in chain2] if chain2 else None}")

# Dump CFG blocks around the and/or chain for context
print("\n=== CFG blocks (and_blk region) ===")
for blk in cfg.get_blocks_in_order():
    last = blk.get_last_instruction()
    if not last:
        continue
    # Only print blocks near the and/or chain
    if and_blk and abs(blk.start_offset - and_blk.start_offset) < 400:
        instrs = []
        for ins in blk.instructions:
            if ins.opname in ('EXTENDED_ARG', 'CACHE', 'NOP', 'RESUME'):
                continue
            instrs.append(f"{ins.offset}:{ins.opname}({ins.argval})")
        succs = [s.start_offset for s in blk.successors]
        print(f"  blk@{blk.start_offset} last={last.opname}({last.argval}) succs={succs}")
        print(f"    {' | '.join(instrs[:6])}")
