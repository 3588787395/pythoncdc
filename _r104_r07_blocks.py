import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
import marshal

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_07_finally_implicit_return.pyc'
with open(path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

func_code = code.co_consts[1]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

region_analyzer = RegionAnalyzer(cfg)
regions = region_analyzer.analyze()

for region in regions:
    if type(region).__name__ == 'TryExceptRegion':
        print(f"TryExceptRegion:")
        print(f"  blocks: {sorted([b.id for b in region.blocks])}")
        print(f"  try_blocks: {sorted([b.id for b in region.try_blocks])}")
        print(f"  else_blocks: {sorted([b.id for b in region.else_blocks])}")
        print(f"  finally_blocks: {sorted([b.id for b in region.finally_blocks])}")
        print(f"  handler_entry_blocks: {sorted([b.id for b in region.handler_entry_blocks])}")
        print(f"  cleanup_blocks: {sorted([b.id for b in region.cleanup_blocks]) if hasattr(region, 'cleanup_blocks') else 'N/A'}")
        print(f"  has_else: {region.has_else}")
        print(f"  has_finally: {region.has_finally}")
        
        # Check if block 10 is in any of these
        block10 = cfg.blocks[10]
        print(f"\n  block 10 in blocks: {block10 in region.blocks}")
        print(f"  block 10 in try_blocks: {block10 in region.try_blocks}")
        print(f"  block 10 in else_blocks: {block10 in region.else_blocks}")
        print(f"  block 10 in finally_blocks: {block10 in region.finally_blocks}")
        print(f"  block 10 in cleanup_blocks: {block10 in region.cleanup_blocks if hasattr(region, 'cleanup_blocks') else False}")
        
        # Check finally_copy_blocks
        if hasattr(region, 'finally_copy_blocks'):
            print(f"  finally_copy_blocks: {region.finally_copy_blocks}")
