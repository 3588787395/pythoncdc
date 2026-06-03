#!/usr/bin/env python3
"""Deep trace for try body generation in match case."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core.cfg.cfg_builder import build_cfg_from_source
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator
from core.cfg.region_analyzer import TryExceptRegion

# Deep patch _generate_try_body
_orig_generate_try_body = RegionASTGenerator._generate_try_body
def _deep_traced_generate_try_body(self, region):
    print(f'  [_generate_try_body] START')
    print(f'  [_generate_try_body] entry={region.entry.start_offset if region.entry else None}')
    print(f'  [_generate_try_body] try_blocks={[b.start_offset for b in region.try_blocks]}')
    print(f'  [_generate_try_body] generated_blocks={sorted(b.start_offset for b in self.generated_blocks)}')
    print(f'  [_generate_try_body] has_finally={region.has_finally}')
    print(f'  [_generate_try_body] handler_entry_blocks={[b.start_offset for b in region.handler_entry_blocks]}')
    
    for block in sorted(region.try_blocks, key=lambda b: b.start_offset):
        print(f'  [_generate_try_body] === Processing try_block {block.start_offset} ===')
        if block in self.generated_blocks:
            print(f'    SKIP: already in generated_blocks')
            continue
        
        # Trace each check
        _fc_keep = region.finally_copy_blocks.get(block.start_offset)
        print(f'    finally_copy_blocks check: _fc_keep={_fc_keep}')
        
        if region.has_finally and block != region.entry:
            print(f'    has_finally check: block != entry, checking succs...')
        else:
            print(f'    has_finally check: skipped (block==entry or no finally)')
        
        # Check nested try regions
        nested_try_regions = []
        for r in self.region_analyzer.regions:
            if isinstance(r, TryExceptRegion) and r is not region:
                is_child = r.parent is region
                is_in_try_blocks = r.entry in set(region.try_blocks)
                print(f'    nested try check: r.entry={r.entry.start_offset if r.entry else None}, is_child={is_child}, is_in_try_blocks={is_in_try_blocks}')
                if is_child or is_in_try_blocks:
                    nested_try_regions.append(r)
        print(f'    nested_try_regions={[r.entry.start_offset for r in nested_try_regions]}')
        
        # Check meaningful instructions
        _meaningful_instrs = [i for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        print(f'    meaningful_instrs={[(i.opname, i.argval) for i in _meaningful_instrs]}')
        
        # Check nested region
        nested_region = self.region_analyzer.get_entry_region_for_block(block)
        print(f'    get_entry_region_for_block({block.start_offset}) = {type(nested_region).__name__ if nested_region else None}')
        if nested_region and nested_region is region:
            print(f'    nested_region is same region, setting to None')
            nested_region = None
        if not nested_region:
            block_region = self.region_analyzer.get_region_for_block(block)
            print(f'    get_region_for_block({block.start_offset}) = {type(block_region).__name__ if block_region else None}')
            if block_region and block_region is not region:
                nested_region = block_region
                print(f'    Using block_region as nested_region')
        if not nested_region:
            for r in self.region_analyzer.regions:
                if r is region:
                    continue
                if isinstance(r, (TryExceptRegion,)):
                    if block in r.blocks:
                        nested_region = r
                        print(f'    Found in region blocks: {type(r).__name__} entry={r.entry.start_offset if r.entry else None}')
                        break
        print(f'    final nested_region={type(nested_region).__name__ if nested_region else None}')
        
        if nested_region and isinstance(nested_region, (TryExceptRegion,)):
            if nested_region is region:
                print(f'    nested_region is same region, will use _generate_block_statements')
            elif nested_region.entry == block:
                print(f'    nested_region.entry == block, will call _generate_region')
            elif block in nested_region.blocks:
                print(f'    block in nested_region.blocks, will mark as generated and skip')
            else:
                print(f'    will use _generate_block_statements')
        elif nested_region is None:
            print(f'    No nested region, will use _generate_block_statements')
    
    result = _orig_generate_try_body(self, region)
    print(f'  [_generate_try_body] RESULT={result}')
    return result

RegionASTGenerator._generate_try_body = _deep_traced_generate_try_body

def decompile(src, name):
    print(f'\n{"="*70}')
    print(f'TEST: {name}')
    print(f'{"="*70}')
    result = build_cfg_from_source(src)
    cfg = result[0] if isinstance(result, (list, tuple)) else result
    gen = RegionASTGenerator(cfg)
    ast_result = gen.generate()
    source = CodeGenerator().generate(ast_result)
    print(f'\nDECOMPILED:\n{source}')

decompile('match x:\n    case 1:\n        try:\n            y = 1\n        except:\n            z = 2\n    case _:\n        pass', 'm054')
