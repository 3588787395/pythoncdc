"""R30 测试工程师：trace why IfRegion entry=182 in share_change is skipped"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion, WithRegion, MatchRegion, RegionType

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find_code(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, type(co)):
            r = find_code(c, name)
            if r:
                return r
    return None

target = find_code(code_obj, 'share_change')
print(f"Found: {target.co_name}")

cfg = build_cfg(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()
regions = analyzer.regions

# Patch generated_blocks to trace additions
gen = RegionASTGenerator(cfg, top_level_code=None)

# Get block 182
block_182 = None
for b in cfg.blocks.values():
    if b.start_offset == 182:
        block_182 = b
        break
    if b.start_offset == 186:
        block_186 = b

# Patch the add to generated_blocks
original_set = gen.generated_blocks
class TracedSet(set):
    def add(self, item):
        if hasattr(item, 'start_offset') and item.start_offset in (182, 186):
            import traceback
            print(f"\n*** generated_blocks.add(block {item.start_offset}) ***")
            traceback.print_stack()
        super().add(item)

gen.generated_blocks = TracedSet()

# Also patch _generate_region to trace
original_generate_region = gen._generate_region
def traced_generate_region(region, skip_store_targets=None):
    if region.entry and region.entry.start_offset in (0, 182, 374):
        print(f"\n=== _generate_region({type(region).__name__} entry={region.entry.start_offset}) ===")
        print(f"  blocks={[b.start_offset for b in region.blocks] if hasattr(region, 'blocks') else 'N/A'}")
        print(f"  block 182 in gen? {block_182 in gen.generated_blocks}")
    result = original_generate_region(region, skip_store_targets=skip_store_targets)
    if region.entry and region.entry.start_offset in (0, 182, 374):
        print(f"  -> result type: {type(result).__name__ if result else 'None'}")
        if isinstance(result, dict):
            print(f"  -> result: {result.get('type')}")
        print(f"  block 182 in gen (after)? {block_182 in gen.generated_blocks}")
    return result

gen._generate_region = traced_generate_region

ast_dict = gen.generate()
print(f"\n=== Final AST ===")
print(f"AST type: {ast_dict.get('type')}")
if 'body' in ast_dict:
    print(f"Body has {len(ast_dict['body'])} statements:")
    for i, stmt in enumerate(ast_dict['body']):
        t = stmt.get('type') if isinstance(stmt, dict) else type(stmt).__name__
        print(f"  [{i}] {t}")
