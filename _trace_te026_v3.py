#!/usr/bin/env python3
"""Debug te026 - detailed trace of _generate_try_body for block 4."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.cfg.cfg_builder import build_cfg_from_source
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import TryExceptRegion, LoopRegion, IfRegion, MatchRegion
from core.cfg.code_generator import CodeGenerator

# Patch _generate_try_body with detailed tracing
_orig = RegionASTGenerator._generate_try_body
def _traced(self, region):
    print(f'[_generate_try_body] entry={region.entry.start_offset}, try_blocks={[b.start_offset for b in region.try_blocks]}')
    for block in region.try_blocks:
        print(f'  Processing try_block {block.start_offset}:')
        if block in self.generated_blocks:
            print(f'    SKIP: already in generated_blocks')
            continue

        # Trace nested region detection
        nested_region = self.region_analyzer.get_entry_region_for_block(block)
        print(f'    get_entry_region_for_block → {type(nested_region).__name__ if nested_region else None}')
        if not nested_region or nested_region is region:
            block_region = self.region_analyzer.get_region_for_block(block)
            print(f'    get_region_for_block → {type(block_region).__name__ if block_region else None}')
            if block_region and block_region is not region and isinstance(block_region, (IfRegion, LoopRegion, TryExceptRegion, MatchRegion)):
                print(f'    block_region is not region: {block_region is not region}')
                if region.entry and region.entry in block_region.blocks:
                    print(f'    region.entry ({region.entry.start_offset}) in block_region.blocks: True')
                    _found_entry = getattr(block_region, 'entry', None)
                    print(f'    block_region.entry: {_found_entry.start_offset if _found_entry else None}')
                    print(f'    block_region.entry in try_blocks: {_found_entry in set(region.try_blocks) if _found_entry else False}')
                    if not _found_entry or _found_entry not in set(region.try_blocks):
                        print(f'    → block_region set to None (outer region)')
                    else:
                        print(f'    → block_region kept (nested region)')
            if block_region and block_region is not region:
                nested_region = block_region
                print(f'    nested_region set to block_region: {type(nested_region).__name__}')
            elif nested_region is region:
                nested_region = None
                print(f'    nested_region set to None (same as region)')
            if nested_region is None:
                print(f'    Entering loop to search regions...')
                for r in self.region_analyzer.regions:
                    if r is region:
                        continue
                    if isinstance(r, (IfRegion, LoopRegion, TryExceptRegion, MatchRegion)):
                        if block in r.blocks or (hasattr(r, 'init_blocks') and block in r.init_blocks):
                            print(f'    Found in {type(r).__name__} (entry={r.entry.start_offset if r.entry else None})')
                            if region.entry and region.entry in r.blocks:
                                print(f'    region.entry ({region.entry.start_offset}) in r.blocks: True')
                                _found_entry = getattr(r, 'entry', None)
                                print(f'    r.entry: {_found_entry.start_offset if _found_entry else None}')
                                print(f'    r.entry in try_blocks: {_found_entry in set(region.try_blocks) if _found_entry else False}')
                                if not _found_entry or _found_entry not in set(region.try_blocks):
                                    print(f'    → SKIPPED (outer region)')
                                    continue
                            nested_region = r
                            print(f'    → nested_region set to {type(r).__name__}')
                            break
                if nested_region is None:
                    print(f'    No nested region found')

        if nested_region:
            print(f'    Final nested_region: {type(nested_region).__name__}')
            if nested_region.entry == block:
                print(f'    nested_region.entry == block → will call _generate_region')
            elif block in nested_region.blocks:
                print(f'    block in nested_region.blocks → will mark as generated and skip')
            else:
                print(f'    → will use _generate_block_statements')
        else:
            print(f'    No nested_region → will use _generate_block_statements')

    result = _orig(self, region)
    print(f'[_generate_try_body] result={result}')
    return result
RegionASTGenerator._generate_try_body = _traced

src = 'try:\n    for i in range(3):\n        print(i)\nexcept:\n    y = 1'
result = build_cfg_from_source(src)
cfg = result[0] if isinstance(result, (list, tuple)) else result
gen = RegionASTGenerator(cfg)
ast_result = gen.generate()
source = CodeGenerator().generate(ast_result)
print(f'\nDECOMPILED:\n{source}')
