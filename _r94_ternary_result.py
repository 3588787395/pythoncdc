#!/usr/bin/env python3
"""R94: Trace _generate_ternary for the get_kline_by_date_one ternary"""
import sys, types, marshal
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion
from core.cfg.region_ast_generator import RegionASTGenerator

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"

def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

orig_code = load_pyc(pyc_path)

def extract_code_objects(code):
    result = {code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

orig_map = extract_code_objects(orig_code)
co = orig_map['get_kline_by_date_one']

cfg = build_cfg(co)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find the target ternary
target_ternary = None
for region in analyzer.regions:
    if isinstance(region, TernaryRegion):
        block_offsets = [b.start_offset for b in region.blocks]
        if 800 in block_offsets:
            target_ternary = region
            break

if target_ternary is None:
    print("Target ternary not found!")
    sys.exit(1)

print(f"Target ternary: entry={target_ternary.entry.start_offset}")
print(f"  condition_block: {target_ternary.condition_block.start_offset}")
print(f"  true_value_block: {target_ternary.true_value_block.start_offset}")
print(f"  false_value_block: {target_ternary.false_value_block.start_offset}")
print(f"  merge_block: {target_ternary.merge_block.start_offset}")
print(f"  value_target: {target_ternary.value_target}")
print(f"  merge_context: {target_ternary.merge_context}")

# Now create the AST generator and call _generate_ternary
gen = RegionASTGenerator(cfg, analyzer)
gen._try_depth = 0
gen._loop_depth = 0
gen._current_loop = None

# Mark the ternary blocks as not generated
gen.generated_blocks = set()
gen.generated_offsets = set()
gen._generated_regions = set()
gen._generating_regions = set()
gen._entry_import_extracted_blocks = set()

# Set up regions list
gen.regions = analyzer.regions

# Call _generate_ternary
gen._generating_regions.add(id(target_ternary))
result = gen._generate_ternary(target_ternary)
gen._generating_regions.discard(id(target_ternary))

print(f"\n_generate_ternary returned: {result}")
if result:
    print(f"  {len(result)} statements:")
    for i, stmt in enumerate(result):
        print(f"    [{i}] type={stmt.get('type')}")
        if stmt.get('type') == 'Assign':
            targets = stmt.get('targets', [])
            for t in targets:
                print(f"        target={t.get('id', t.get('type'))}")
            val = stmt.get('value', {})
            print(f"        value type={val.get('type')}")
        elif stmt.get('type') == 'Expr':
            val = stmt.get('value', {})
            print(f"        value type={val.get('type')}")
else:
    print("  None!")
