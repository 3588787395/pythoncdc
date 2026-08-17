#!/usr/bin/env python3
"""Debug: trace what happens during async function decompilation."""
import sys, os, types, marshal, dis
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

REPRO_DIR = PROJECT_ROOT / '.trae' / 'specs' / 'region-comprehensive-pyc-10rounds' / 'rounds' / 'round_01' / 'test_engineer' / 'minimal_repros'

pyc_path = REPRO_DIR / 'repro_10_as1_async_await_body.pyc'

with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find the 'test' function code object
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test':
        test_code = const
        break

# Build CFG and analyze
cfg = build_cfg(test_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f"is_generator_entry: {analyzer.metadata.get('is_generator_entry')}")
print(f"generator_entry_block: {analyzer.metadata.get('generator_entry_block')}")
print(f"entry_block: {cfg.entry_block.start_offset if cfg.entry_block else None}")
print(f"Regions: {len(regions)}")
for r in regions:
    print(f"  type={r.region_type}, entry={r.entry.start_offset if r.entry else None}, parent={type(r.parent).__name__ if r.parent else None}")

# Generate AST
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()

print(f"\nGenerated AST: {ast_dict}")
print(f"Generated blocks: {[b.start_offset for b in gen.generated_blocks]}")
print(f"Generated offsets: {sorted(gen.generated_offsets)}")
