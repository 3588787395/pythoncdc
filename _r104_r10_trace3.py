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

# Call _generate_handler_body_statements on block 16
block16 = cfg.blocks[16]

# Manually trace the method by reading its source and adding prints
# Instead, let's check what handler_instrs looks like
handler_instrs = [i for i in block16.instructions
                  if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
                                       'PUSH_EXC_INFO', 'POP_EXCEPT', 'POP_TOP',
                                       'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
                                       'WITH_EXCEPT_START', 'EXTENDED_ARG')]
print(f"handler_instrs: {[(i.opname, i.arg, getattr(i, 'argval', None)) for i in handler_instrs]}")

store_indices = [i for i, instr in enumerate(handler_instrs)
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')]
print(f"store_indices: {store_indices}")

# Check _find_return_through_cleanup_chain
has_return_chain = ast_gen._find_return_through_cleanup_chain(block16)
print(f"_find_return_through_cleanup_chain: {has_return_chain}")

# Check _find_return_chain_via_successors
has_return_chain_via_succ = ast_gen._find_return_chain_via_successors(block16)
print(f"_find_return_chain_via_successors: {has_return_chain_via_succ}")

# Now call the method
result = ast_gen._generate_handler_body_statements(block16)
print(f"\nResult: {result}")
