"""Check _generate_block_statements for block 148"""
import sys, marshal, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

pyc_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_07_finally_implicit_return.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func_code = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_finally_implicit_return':
        func_code = c
        break

cfg = build_cfg(func_code)
gen = RegionASTGenerator(cfg)
gen.regions = gen.region_analyzer.analyze()

block_148 = cfg.get_block_by_offset(148)
print(f"Block 148 instructions: {[(i.opname, i.argval) for i in block_148.instructions]}")
print(f"Block 148 in generated_blocks: {block_148 in gen.generated_blocks}")
print(f"148 in generated_offsets: {148 in gen.generated_offsets}")

# Clear generated markers
gen.generated_blocks.discard(block_148)
gen.generated_offsets.discard(148)

# Now try _generate_block_statements
ebs = gen._generate_block_statements(block_148)
print(f"_generate_block_statements(block 148): {json.dumps(ebs, default=str)}")

# Also check: what's the block role?
role = gen.region_analyzer.get_block_role(block_148)
print(f"Block 148 role: {role}")

# Check if there's a Region for block 148
for r in gen.regions:
    if r.entry == block_148:
        print(f"Region entry=148: {type(r).__name__}, region_type={r.region_type}")
        # Check if _generate_region returns something
        result = gen._generate_region(r)
        print(f"_generate_region: {json.dumps(result, default=str)}")
