"""R30 测试工程师：调试share_change的region结构"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# Find share_change code object
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

print(f"\n=== Regions ({len(regions)}) ===")
for r in regions:
    print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None} blocks={[b.start_offset for b in r.blocks] if hasattr(r, 'blocks') else 'N/A'}")

# Print blocks
print(f"\n=== CFG Blocks (offset <= 300) ===")
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    if b.start_offset > 300:
        continue
    print(f"\nBlock {b.start_offset}:")
    for i in b.instructions:
        print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
    print(f"  preds: {[p.start_offset for p in b.predecessors]}")
    print(f"  succs: {[s.start_offset for s in b.successors]}")
    r = analyzer.get_region_for_block(b)
    er = analyzer.get_entry_region_for_block(b)
    print(f"  region: {type(r).__name__ if r else None} entry={r.entry.start_offset if r and r.entry else None}")
    print(f"  entry_region: {type(er).__name__ if er else None} entry={er.entry.start_offset if er and er.entry else None}")

# Generate AST and inspect
print(f"\n=== AST Generation ===")
gen = RegionASTGenerator(cfg, top_level_code=None)

# Check top-level regions before generation (use already-analyzed regions)
top_level = [r for r in regions if r.parent is None]
print(f"\nTop-level regions (parent is None): {len(top_level)}")
for r in sorted(top_level, key=lambda x: x.entry.start_offset if x.entry else 0):
    print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None} blocks={[b.start_offset for b in r.blocks] if hasattr(r, 'blocks') else 'N/A'}")

# Check if block 182 is in generated_blocks after generation
ast_dict = gen.generate()
print(f"\nAST type: {ast_dict.get('type')}")
if 'body' in ast_dict:
    print(f"Body has {len(ast_dict['body'])} statements:")
    for i, stmt in enumerate(ast_dict['body']):
        t = stmt.get('type') if isinstance(stmt, dict) else type(stmt).__name__
        print(f"  [{i}] {t}")
        if isinstance(stmt, dict) and 'test' in stmt:
            test_str = str(stmt['test'])[:100]
            print(f"       test: {test_str}")

# Check generated_blocks
print(f"\n=== generated_blocks contains 182? ===")
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    if b.start_offset in (182, 186, 268, 122, 162):
        in_gen = b in gen.generated_blocks
        print(f"  Block {b.start_offset}: in generated_blocks = {in_gen}")
