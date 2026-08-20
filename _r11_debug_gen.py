"""Debug block role and finally_copy handling for repro_r11_06."""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')

import marshal
import types

with open('.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_11/test_engineer/minimal_repros/repro_r11_06_try_except_finally_continue.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

builder = CFGBuilder()
cfg = builder.build(code)

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Find the try region
try_region = None
for r in regions:
    if type(r).__name__ == 'TryExceptRegion':
        try_region = r
        break

print(f"TryExceptRegion: entry={try_region.entry.start_offset}")
print(f"  finally_copy_blocks: {try_region.finally_copy_blocks}")
print(f"  has_finally: {try_region.has_finally}")

# Check find_enclosing_region for block 84 and 122
for offset in [84, 122]:
    block = cfg.get_block_by_offset(offset)
    region = analyzer.find_enclosing_region(block, 'try_finally', require_finally=True)
    print(f"\nBlock @{offset}:")
    print(f"  find_enclosing_region(try_finally, require_finally=True): {type(region).__name__ if region else None}")
    if region:
        print(f"  region.has_finally: {region.has_finally}")
        print(f"  finally_copy_blocks.get({offset}): {region.finally_copy_blocks.get(offset)}")

# Now generate AST
gen = RegionASTGenerator(cfg, analyzer)
ast_result = gen.generate()

# Print the generated source
import ast
if 'ast' in ast_result:
    tree = ast_result['ast']
    source = ast.unparse(tree)
    print(f"\n=== Generated source ===")
    print(source)
