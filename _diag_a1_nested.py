import sys, os, dis, types
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion

# A1: nested try with IndexError/AttributeError
source = 'try:\n    try:\n        pass\n    except IndexError:\n        pass\nexcept AttributeError:\n    pass'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

gen = RegionASTGenerator(cfg)

# Check which regions are found and their relationships
regions = gen.region_analyzer.analyze()
print("REGIONS:")
for i, r in enumerate(regions):
    if isinstance(r, TryExceptRegion):
        print(f"  Region[{i}]: try_offset={r.try_offset_start}-{r.try_offset_end}, handlers={r.except_handlers}, parent={type(r.parent).__name__ if r.parent else None}")
        print(f"    handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}")
        print(f"    try_blocks={[b.start_offset for b in r.try_blocks]}")
        print(f"    all blocks={[b.start_offset for b in r.blocks]}")

# Now check what _generate_try_body finds as nested_try_regions
region1 = regions[0]  # IndexError region
region2 = regions[1]  # AttributeError region

print(f"\nRegion1 (IndexError): try_offset={region1.try_offset_start}-{region1.try_offset_end}")
print(f"Region2 (AttributeError): try_offset={region2.try_offset_start}-{region2.try_offset_end}")
print(f"Region2.parent is Region1: {region2.parent is region1}")
print(f"Region1.parent is Region2: {region1.parent is region2}")

# Check the nested detection logic
for r in regions:
    if isinstance(r, TryExceptRegion) and r is not region1:
        is_child = r.parent is region1
        is_in_try_blocks = r.entry in set(region1.try_blocks)
        handler_in_range = False
        for heb in r.handler_entry_blocks:
            if region1.try_offset_start <= heb.start_offset < region1.try_offset_end:
                handler_in_range = True
                break
        is_before_try_start = r.entry.start_offset < region1.try_offset_start and r.try_offset_end > region1.try_offset_start
        is_nested = is_child or is_in_try_blocks or is_before_try_start or handler_in_range
        nested_is_smaller = r.try_offset_end - r.try_offset_start < region1.try_offset_end - region1.try_offset_start
        print(f"\n  Checking if Region2 is nested in Region1:")
        print(f"    is_child={is_child}, is_in_try_blocks={is_in_try_blocks}, handler_in_range={handler_in_range}, is_before_try_start={is_before_try_start}")
        print(f"    is_nested={is_nested}, nested_is_smaller={nested_is_smaller}")
        print(f"    Will be added as nested: {is_nested and (r.parent is None or r.parent is region1) and (nested_is_smaller or is_child)}")
