"""Debug handler type classification."""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')

import marshal
import types

with open('.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_11/test_engineer/minimal_repros/repro_r11_06_try_except_finally_continue.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

builder = CFGBuilder()
cfg = builder.build(code)

# Parse exception table
analyzer = RegionAnalyzer(cfg)
handler_infos = analyzer._parse_exception_table()

print("Handler infos:")
for i, info in enumerate(handler_infos):
    print(f"  [{i}] try=[{info['try_start']},{info['try_end']}), handler_start={info['handler_start']}, type={info['handler_type']}, depth={info['depth']}")

# Now run analyze
analyzer.analyze()

print(f"\nRegions ({len(analyzer.regions)}):")
for i, r in enumerate(analyzer.regions):
    blocks_str = [b.start_offset for b in r.blocks]
    print(f"  Region {i}: {type(r).__name__}: entry={r.entry.start_offset}, blocks={blocks_str}")
    if hasattr(r, 'body_blocks') and r.body_blocks:
        print(f"    body_blocks: {[b.start_offset for b in r.body_blocks]}")
    if hasattr(r, 'cleanup_blocks') and r.cleanup_blocks:
        print(f"    cleanup_blocks: {[b.start_offset for b in r.cleanup_blocks]}")
    if hasattr(r, 'finally_copy_blocks') and r.finally_copy_blocks:
        print(f"    finally_copy_blocks: {r.finally_copy_blocks}")
    if hasattr(r, 'has_finally'):
        print(f"    has_finally: {r.has_finally}")
    if hasattr(r, 'else_blocks') and r.else_blocks:
        print(f"    else_blocks: {[b.start_offset for b in r.else_blocks]}")
