import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
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

# Check block 10
block10 = cfg.blocks[10]
print(f"Block 10: offset={block10.start_offset}, instrs={[(i.opname, i.arg) for i in block10.instructions]}")
print(f"  in generated_blocks: {block10 in region_analyzer.generated_blocks if hasattr(region_analyzer, 'generated_blocks') else 'N/A'}")

# Check which region owns block 10
for region in regions:
    if block10 in region.blocks:
        print(f"  owned by: {type(region).__name__}, entry={region.entry.id}")
        break

# Check block_to_region mapping
owner = region_analyzer.block_to_region.get(block10)
print(f"  block_to_region: {type(owner).__name__ if owner else None}")

# Generate AST
ast_gen = RegionASTGenerator(cfg, region_analyzer, regions)
ast = ast_gen.generate()
print(f"\nAST body: {ast.get('body')}")

# Check if block 10 is in generated_blocks after AST generation
print(f"\nAfter generation:")
print(f"  block 10 in generated_blocks: {block10 in ast_gen.generated_blocks}")
