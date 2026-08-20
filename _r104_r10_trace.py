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

# Monkey-patch _generate_handler_body_statements to trace
ast_gen = RegionASTGenerator(cfg, region_analyzer, regions)

original_gen_handler = ast_gen._generate_handler_body_statements
def traced_gen_handler(block):
    result = original_gen_handler(block)
    if result:
        print(f"  _generate_handler_body_statements(block {block.id}): {result}")
    return result
ast_gen._generate_handler_body_statements = traced_gen_handler

# Also trace _generate_block_statements
original_gen_block = ast_gen._generate_block_statements
def traced_gen_block(block):
    result = original_gen_block(block)
    if result:
        print(f"  _generate_block_statements(block {block.id}): {result}")
    return result
ast_gen._generate_block_statements = traced_gen_block

# Generate AST
ast = ast_gen.generate()
print(f"\nFinal AST: {ast}")
