#!/usr/bin/env python3
"""Debug: dump IfRegion@1686 children and BoolOp dual-role analysis."""
import sys, types
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, TernaryRegion, LoopRegion

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
cfg = build_cfg(f)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print("=== Regions around offset 1686-2082 ===")
for r in regions:
    entry_off = r.entry.start_offset if getattr(r, 'entry', None) else None
    if entry_off is None:
        continue
    if 1680 <= entry_off <= 2090:
        rtype = type(r).__name__
        blocks_offs = [b.start_offset for b in (getattr(r, 'blocks', None) or [])]
        then_offs = [b.start_offset for b in (getattr(r, 'then_blocks', None) or [])]
        merge_off = getattr(r, 'merge_block', None)
        merge_off = merge_off.start_offset if merge_off else None
        val_tgt = getattr(r, 'value_target', None)
        children = getattr(r, 'children', [])
        ch_strs = [f"{type(ch).__name__}@{ch.entry.start_offset}" for ch in children if getattr(ch, 'entry', None)]
        print(f"  {rtype} entry={entry_off} merge={merge_off} val_tgt={val_tgt}")
        print(f"     blocks={blocks_offs}")
        print(f"     then_blocks={then_offs}")
        print(f"     children={ch_strs}")

print("\n=== block_to_region for offsets 1686-2082 ===")
b2r = getattr(analyzer, 'block_to_region', {})
_all_blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
for blk in sorted(_all_blocks, key=lambda b: b.start_offset):
    if 1686 <= blk.start_offset <= 2082:
        owner = b2r.get(blk)
        owner_str = type(owner).__name__ + f"@{owner.entry.start_offset}" if (owner and getattr(owner, 'entry', None)) else (type(owner).__name__ if owner else "None")
        print(f"  blk@{blk.start_offset:5d}: owner={owner_str}")

print("\n=== BoolOpRegions with entry/merge in range ===")
for r in regions:
    if not isinstance(r, BoolOpRegion):
        continue
    entry_off = r.entry.start_offset if r.entry else None
    merge_off = r.merge_block.start_offset if r.merge_block else None
    if (entry_off and 1680 <= entry_off <= 2090) or (merge_off and 1680 <= merge_off <= 2090):
        blocks_offs = [b.start_offset for b in r.blocks]
        print(f"  BoolOpRegion entry={entry_off} merge={merge_off} val_tgt={r.value_target} blocks={blocks_offs}")
        # Check if entry is also another BoolOpRegion's merge
        for r2 in regions:
            if isinstance(r2, BoolOpRegion) and r2 is not r:
                if r2.merge_block and r2.merge_block.start_offset == entry_off:
                    print(f"    -> entry {entry_off} is ALSO merge of BoolOpRegion@{r2.entry.start_offset} (val_tgt={r2.value_target})")

print("\n=== IfRegion@1686 children (full dump) ===")
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 1686:
        children = getattr(r, 'children', [])
        print(f"  IfRegion@1686 children count={len(children)}")
        for ch in children:
            ch_entry = ch.entry.start_offset if getattr(ch, 'entry', None) else None
            print(f"    {type(ch).__name__}@{ch_entry}")
