#!/usr/bin/env python3
"""Debug: dump region structure for load_bars_from_hundsun."""
import sys, types
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, TernaryRegion

m = load_pyc_file_v2('/workspace/quotation.pyc')
c = m.code.get() if hasattr(m.code, 'get') else m.code
if hasattr(c, 'to_python_code'):
    c = c.to_python_code()

def find(co, n):
    if co.co_name == n:
        return co
    for k in co.co_consts:
        if isinstance(k, types.CodeType):
            r = find(k, n)
            if r:
                return r
    return None

f = find(c, 'load_bars_from_hundsun')
print(f"=== found code object: {f.co_name} ===")

cfg = build_cfg(f)
print(f"=== CFG blocks (by start_offset) ===")
_all_blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
for blk in sorted(_all_blocks, key=lambda b: b.start_offset):
    last = blk.get_last_instruction() if hasattr(blk, 'get_last_instruction') else None
    last_str = f"{last.opname}->{last.argval}" if last else "None"
    first_meaningful = None
    for ins in blk.instructions:
        if ins.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
            first_meaningful = ins
            break
    fm_str = f"{first_meaningful.offset}:{first_meaningful.opname}({first_meaningful.argval})" if first_meaningful else "?"
    print(f"  blk@{blk.start_offset:5d} .. end={last_str:40s} first={fm_str}")

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
print(f"\n=== {len(regions)} regions ===")
for r in regions:
    entry_off = r.entry.start_offset if getattr(r, 'entry', None) else None
    cond_off = r.condition_block.start_offset if getattr(r, 'condition_block', None) else None
    rtype = type(r).__name__
    rt_name = getattr(getattr(r, 'region_type', None), 'name', '')
    then_offs = [b.start_offset for b in (getattr(r, 'then_blocks', None) or [])]
    else_offs = [b.start_offset for b in (getattr(r, 'else_blocks', None) or [])]
    blocks_offs = [b.start_offset for b in (getattr(r, 'blocks', None) or [])]
    merge_off = getattr(r, 'merge_block', None)
    merge_off = merge_off.start_offset if merge_off else None
    val_tgt = getattr(r, 'value_target', None)
    print(f"  {rtype}({rt_name}) entry={entry_off} cond={cond_off} merge={merge_off} val_tgt={val_tgt}")
    print(f"     blocks={blocks_offs}")
    if then_offs:
        print(f"     then_blocks={then_offs}")
    if else_offs:
        print(f"     else_blocks={else_offs}")
    elif hasattr(r, 'elif_conditions'):
        elc = [b.start_offset for b in (getattr(r, 'elif_conditions', None) or [])]
        elb = [[b.start_offset for b in body] for body in (getattr(r, 'elif_bodies', None) or [])]
        elf = [b.start_offset for b in (getattr(r, 'elif_final_else', None) or [])]
        if elc:
            print(f"     elif_conditions={elc}")
        if elb:
            print(f"     elif_bodies={elb}")
        if elf:
            print(f"     elif_final_else={elf}")

print(f"\n=== block_to_region for relevant offsets ===")
relevant = [78, 152, 166, 208, 214, 226, 256, 270, 286, 348, 400, 402, 422, 424, 446, 606, 710, 824]
b2r = getattr(analyzer, 'block_to_region', {})
for off in relevant:
    blk = cfg.get_block_by_offset(off)
    if blk is None:
        print(f"  offset {off}: NO BLOCK")
        continue
    owner = b2r.get(blk)
    owner_str = type(owner).__name__ + f"@{owner.entry.start_offset}" if (owner and getattr(owner, 'entry', None)) else (type(owner).__name__ if owner else "None")
    entry_r = analyzer.get_entry_region_for_block(blk)
    entry_r_str = type(entry_r).__name__ + f"@{entry_r.entry.start_offset}" if (entry_r and getattr(entry_r, 'entry', None)) else (type(entry_r).__name__ if entry_r else "None")
    print(f"  offset {off:5d}: owner={owner_str:30s} entry_region={entry_r_str}")

print(f"\n=== IfRegion children ===")
for r in regions:
    if isinstance(r, IfRegion):
        entry_off = r.entry.start_offset if r.entry else None
        children = getattr(r, 'children', [])
        ch_strs = []
        for ch in children:
            ch_entry = ch.entry.start_offset if getattr(ch, 'entry', None) else None
            ch_strs.append(f"{type(ch).__name__}@{ch_entry}")
        print(f"  IfRegion@{entry_off} children={ch_strs}")
