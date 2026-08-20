"""Trace region structure for exception_handling_complex"""
import sys
sys.path.insert(0, '.')

from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder
import marshal

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
f.close()

# Find exception_handling_complex
import types
for c in code.co_consts:
    if isinstance(c, types.CodeType):
        for cc in c.co_consts:
            if isinstance(cc, types.CodeType) and cc.co_name == 'exception_handling_complex':
                target_code = cc
                break

print(f"Found: {target_code.co_name}")
print(f"varnames: {target_code.co_varnames}")

# Build CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target_code)

# Build regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print(f"\n=== Regions ({len(analyzer.regions)}) ===")
for i, r in enumerate(analyzer.regions):
    rtype = type(r).__name__
    entry = r.entry.start_offset if r.entry else None
    try_start = getattr(r, 'try_offset_start', None)
    try_end = getattr(r, 'try_offset_end', None)
    has_finally = getattr(r, 'has_finally', False)
    has_else = bool(getattr(r, 'else_blocks', None))
    
    try_blocks = [b.start_offset for b in getattr(r, 'try_blocks', [])]
    else_blocks = [b.start_offset for b in getattr(r, 'else_blocks', []) or []]
    finally_blocks = [b.start_offset for b in getattr(r, 'finally_blocks', []) or []]
    handler_entries = [b.start_offset for b in getattr(r, 'handler_entry_blocks', [])]
    finally_copy = getattr(r, 'finally_copy_blocks', {})
    
    print(f"\nRegion {i}: {rtype}")
    print(f"  entry: {entry}")
    print(f"  try_offset: {try_start}-{try_end}")
    print(f"  has_finally: {has_finally}, has_else: {has_else}")
    print(f"  try_blocks: {try_blocks}")
    print(f"  else_blocks: {else_blocks}")
    print(f"  finally_blocks: {finally_blocks}")
    print(f"  handler_entries: {handler_entries}")
    if finally_copy:
        print(f"  finally_copy_blocks: {dict(finally_copy)}")
    
    # Print all blocks in region
    all_blocks = [b.start_offset for b in r.blocks]
    print(f"  all_blocks: {all_blocks}")
