#!/usr/bin/env python3
"""Check IfRegion@0 and IfRegion@152 children to understand dual-role scope."""
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
cfg = build_cfg(f)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print("=== IfRegion@0 and @152 children ===")
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset in (0, 152, 1686):
        entry_off = r.entry.start_offset
        children = getattr(r, 'children', [])
        print(f"\n  IfRegion@{entry_off} children count={len(children)}:")
        for ch in children:
            ch_entry = ch.entry.start_offset if getattr(ch, 'entry', None) else None
            ch_merge = ch.merge_block.start_offset if getattr(ch, 'merge_block', None) else None
            ch_vt = getattr(ch, 'value_target', None)
            # Check enclosing parent
            enc = ch.find_enclosing_parent((IfRegion, type(r)))
            enc_str = f"IfRegion@{enc.entry.start_offset}" if (enc and getattr(enc, 'entry', None)) else (type(enc).__name__ if enc else "None")
            print(f"    {type(ch).__name__}@{ch_entry} merge={ch_merge} val_tgt={ch_vt} enclosing_parent={enc_str}")

print("\n=== All BoolOpRegions with dual-role (merge == another BoolOp entry) ===")
for r in regions:
    if not isinstance(r, BoolOpRegion):
        continue
    for r2 in regions:
        if isinstance(r2, BoolOpRegion) and r2 is not r:
            if r.merge_block and r.merge_block is r2.entry:
                r_enc = r.find_enclosing_parent((IfRegion,))
                r2_enc = r2.find_enclosing_parent((IfRegion,))
                r_enc_str = f"IfRegion@{r_enc.entry.start_offset}" if (r_enc and getattr(r_enc, 'entry', None)) else "None"
                r2_enc_str = f"IfRegion@{r2_enc.entry.start_offset}" if (r2_enc and getattr(r2_enc, 'entry', None)) else "None"
                print(f"  BoolOp@{r.entry.start_offset} merge={r.merge_block.start_offset} enc={r_enc_str} -> BoolOp@{r2.entry.start_offset} enc={r2_enc_str}")
