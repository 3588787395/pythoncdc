import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
import marshal

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_10_try_wrap_for_else_break.pyc'
with open(path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

func_code = code.co_consts[1]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

region_analyzer = RegionAnalyzer(cfg)
regions = region_analyzer.analyze()

ast_gen = RegionASTGenerator(cfg, region_analyzer, regions)

# Monkey-patch expr_reconstructor.reconstruct to trace
original_reconstruct = ast_gen.expr_reconstructor.reconstruct
def traced_reconstruct(instrs):
    result = original_reconstruct(instrs)
    print(f"  reconstruct({[(i.opname, i.arg) for i in instrs]}): {result}")
    return result
ast_gen.expr_reconstructor.reconstruct = traced_reconstruct

# Monkey-patch _build_statement
original_build = ast_gen._build_statement
def traced_build(instrs):
    result = original_build(instrs)
    print(f"  _build_statement({[(i.opname, i.arg) for i in instrs]}): {result}")
    return result
ast_gen._build_statement = traced_build

# Now call _generate_handler_body_statements on block 16
block16 = cfg.blocks[16]
print(f"Block 16 instructions: {[(i.opname, i.arg) for i in block16.instructions]}")
print(f"\nCalling _generate_handler_body_statements(block 16)...")
result = ast_gen._generate_handler_body_statements(block16)
print(f"\nResult: {result}")
