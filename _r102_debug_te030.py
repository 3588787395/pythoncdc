#!/usr/bin/env python3
"""Debug: check try-except-finally exception table."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.cfg import build_cfg
from core.cfg.dominator_analyzer import DominatorAnalyzer
from core.cfg.region_analyzer import RegionAnalyzer

code_str = 'try:\n    x = 1\nexcept:\n    y = 2\nfinally:\n    z = 3'
code = compile(code_str, '<tef>', 'exec')

cfg = build_cfg(code)
print("Raw exception_table entries:")
for e in cfg.exception_table:
    print(f"  start={e.get('start')} end={e.get('end')} target={e.get('target')} depth={e.get('depth')}")

dom = DominatorAnalyzer(cfg)
dom.analyze()
analyzer = RegionAnalyzer(cfg, dom)
hi = analyzer._parse_exception_table()
print(f"\nParsed handler_infos: {len(hi)}")
for info in hi:
    print(f"  try=[{info['try_start']},{info['try_end']}) handler={info['handler_start']} type={info.get('handler_type')}")

regions = analyzer.analyze()
print(f"\nRegions: {len(regions)}")
for r in regions:
    rt = type(r).__name__
    eo = r.entry.start_offset if r.entry else None
    print(f"  {rt}: entry={eo}")
    if hasattr(r, 'try_offset_start'):
        print(f"    try_offset: [{r.try_offset_start}, {r.try_offset_end})")
    if hasattr(r, 'except_handlers') and r.except_handlers:
        for i, h in enumerate(r.except_handlers):
            print(f"    handler[{i}]: blocks={[b.start_offset for b in h[2]]}")
    if hasattr(r, 'finally_blocks') and r.finally_blocks:
        print(f"    finally_blocks: {[b.start_offset for b in r.finally_blocks]}")
