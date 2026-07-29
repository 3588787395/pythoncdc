"""R30 调试 get_block_stocks 的循环体生成流程"""
import sys
import dis
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target = None
for const in code_obj.co_consts:
    if isinstance(const, type(code_obj)) and const.co_name == 'get_block_stocks':
        target = const
        break

builder = CFGBuilder()
cfg = builder.build(target)

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Find the LoopRegion
loop_region = None
for r in regions:
    if isinstance(r, LoopRegion):
        loop_region = r
        break

print(f"=== LoopRegion properties ===")
print(f"  blocks: {sorted(b.start_offset for b in r.blocks)}")
print(f"  entry: {loop_region.entry.start_offset if loop_region.entry else None}")
print(f"  header_block: {loop_region.header_block.start_offset if loop_region.header_block else None}")
print(f"  condition_block: {loop_region.condition_block.start_offset if loop_region.condition_block else None}")
print(f"  back_edge_block: {loop_region.back_edge_block.start_offset if loop_region.back_edge_block else None}")
print(f"  body_blocks: {sorted(b.start_offset for b in loop_region.body_blocks) if loop_region.body_blocks else None}")
print(f"  else_blocks: {sorted(b.start_offset for b in loop_region.else_blocks) if loop_region.else_blocks else None}")
print(f"  metadata keys: {list(loop_region.metadata.keys())}")
print(f"  natural_back_edge: {loop_region.metadata.get('natural_back_edge')}")
if loop_region.metadata.get('natural_back_edge'):
    nbe = loop_region.metadata['natural_back_edge']
    print(f"    natural_back_edge.start_offset: {nbe.start_offset}")

# Check block roles
print(f"\n=== Block roles ===")
for b in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    role = analyzer.get_block_role(b)
    print(f"  block {b.start_offset}: role={role}")

# Now trace the AST generation
print(f"\n=== Tracing AST generation ===")
gen = RegionASTGenerator(cfg, analyzer, target)

# Patch _loop_dispatch_block to trace
orig_dispatch = gen._loop_dispatch_block
def traced_dispatch(block, region, child_info, boolop_for_while, body_stmts, body_blocks_no_header, back_edge_stmts, natural_back_edge, back_edge_source_blocks=None):
    print(f"  _loop_dispatch_block: block={block.start_offset}, is_header={block==region.header_block}, is_cond={block==region.condition_block}, is_nbe={block==natural_back_edge}, natural_back_edge={natural_back_edge.start_offset if natural_back_edge else None}")
    result = orig_dispatch(block, region, child_info, boolop_for_while, body_stmts, body_blocks_no_header, back_edge_stmts, natural_back_edge, back_edge_source_blocks)
    print(f"    -> handled={result}, body_stmts={len(body_stmts)}, back_edge_stmts={len(back_edge_stmts)}, body_blocks_no_header={[b.start_offset for b in body_blocks_no_header]}")
    return result
gen._loop_dispatch_block = traced_dispatch

# Patch _loop_process_natural_back_edge to trace
orig_nbe = gen._loop_process_natural_back_edge
def traced_nbe(block, back_edge_stmts, back_edge_source_blocks=None):
    print(f"  _loop_process_natural_back_edge: block={block.start_offset}")
    result = orig_nbe(block, back_edge_stmts, back_edge_source_blocks)
    print(f"    -> result={result}, back_edge_stmts={len(back_edge_stmts)}")
    return result
gen._loop_process_natural_back_edge = traced_nbe

# Patch _loop_process_back_edge_with_condition
orig_be = gen._loop_process_back_edge_with_condition
def traced_be(block, region, back_edge_stmts, back_edge_source_blocks=None):
    print(f"  _loop_process_back_edge_with_condition: block={block.start_offset}")
    orig_be(block, region, back_edge_stmts, back_edge_source_blocks)
    print(f"    -> back_edge_stmts={len(back_edge_stmts)}")
gen._loop_process_back_edge_with_condition = traced_be

# Patch _loop_extract_pre_stmts_from_instrs
orig_extract = gen._loop_extract_pre_stmts_from_instrs
def traced_extract(instrs, block):
    print(f"  _loop_extract_pre_stmts_from_instrs: block={block.start_offset}, num_instrs={len(instrs)}")
    print(f"    instrs: {[(i.opname, i.argval) for i in instrs[:15]]}")
    result = orig_extract(instrs, block)
    print(f"    -> {len(result)} stmts: {[s.get('type') for s in result]}")
    return result
gen._loop_extract_pre_stmts_from_instrs = traced_extract

# Generate the loop
ast = gen._generate_region(loop_region)
if ast:
    import json
    print(f"\n=== Generated AST ===")
    print(json.dumps(ast, indent=2, default=str)[:3000])
