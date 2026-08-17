#!/usr/bin/env python3
"""R92 check get_multiminute_his_data IfRegion structure"""
import sys, marshal, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_multiminute_his_data')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

for r in regions:
    if isinstance(r, IfRegion):
        mb = r.merge_block.start_offset if r.merge_block else None
        rt = r.region_type.name if hasattr(r, 'region_type') else '?'
        print(f"IfRegion@{r.entry.start_offset} type={rt} merge={mb} "
              f"then={len(r.then_blocks or [])} else={len(r.else_blocks or [])} "
              f"blocks={len(r.blocks)}")
        if hasattr(r, 'elif_conditions') and r.elif_conditions:
            print(f"  elif_conds={[b.start_offset for b in r.elif_conditions]}")
            print(f"  elif_bodies_len={[len(b) for b in r.elif_bodies] if r.elif_bodies else []}")
        # Check if merge_block is in blocks
        if mb is not None:
            post_mb = [b.start_offset for b in r.blocks if b.start_offset > mb]
            if post_mb:
                print(f"  blocks_after_merge={post_mb[:10]}...")

# Also check block at offset around idx=160
# idx=160 in the original bytecode corresponds to some offset
# Let me find the block that contains the JUMP_FORWARD
import dis
orig_instrs = list(dis.get_instructions(func_code))
if len(orig_instrs) > 161:
    jf_instr = orig_instrs[160]
    print(f"\nOriginal instruction at idx=160: offset={jf_instr.offset} {jf_instr.opname} {jf_instr.argrepr}")
    # Find the block containing this instruction
    for block in cfg.blocks.values():
        for instr in block.instructions:
            if instr.offset == jf_instr.offset:
                print(f"  Block@{block.start_offset} contains this instruction")
                print(f"  Block predecessors: {[p.start_offset for p in block.predecessors]}")
                print(f"  Block successors: {[s.start_offset for s in block.successors]}")
                # Check which region owns this block
                owner = analyzer.get_region_for_block(block)
                print(f"  Owner region: {type(owner).__name__ if owner else 'None'}")
                if owner and hasattr(owner, 'entry'):
                    print(f"  Owner entry: {owner.entry.start_offset if owner.entry else '?'}")
                break
