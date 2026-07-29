"""R23-N9 详细跟踪 one_prod_to_dataframe 的生成过程"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

import types
target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'one_prod_to_dataframe':
        target = const
        break

builder = CFGBuilder()
cfg = builder.build(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Patch _generate_block_statements and _loop_generate_for to trace
generator = RegionASTGenerator(cfg, analyzer, target)

orig_generate_block_statements = generator._generate_block_statements
orig_loop_generate_for = generator._loop_generate_for
orig_process_if_blocks = generator._process_if_blocks if hasattr(generator, '_process_if_blocks') else None

def traced_generate_block_statements(block, *args, **kwargs):
    if block.start_offset in (340, 348):
        import traceback
        print(f"\n>>> _generate_block_statements(block@{block.start_offset})")
        traceback.print_stack(limit=8)
    return orig_generate_block_statements(block, *args, **kwargs)

def traced_loop_generate_for(region, *args, **kwargs):
    print(f"\n>>> _loop_generate_for(region entry={region.entry.start_offset if region.entry else None})")
    return orig_loop_generate_for(region, *args, **kwargs)

generator._generate_block_statements = traced_generate_block_statements
generator._loop_generate_for = traced_loop_generate_for

# Now generate
result = generator.generate()

# Find the relevant part
import json
print("\n=== Generated AST (first 5 statements) ===")
stmts = result.get('body', result) if isinstance(result, dict) else result
if isinstance(stmts, dict) and 'body' in stmts:
    stmts = stmts['body']
for i, stmt in enumerate(stmts[:15]):
    print(f"\n[{i}] type={stmt.get('type')}")
    if stmt.get('type') == 'Assign':
        print(f"    targets={[t.get('id') if t.get('type')=='Name' else t.get('type') for t in stmt.get('targets',[])]}")
        v = stmt.get('value', {})
        print(f"    value={v.get('type')} {repr(v.get('value', v.get('id', '')))[:50]}")
    elif stmt.get('type') == 'Expr':
        v = stmt.get('value', {})
        print(f"    value={v.get('type')} {repr(v.get('id', v.get('value', '')))[:50]}")
    elif stmt.get('type') == 'For':
        print(f"    target={stmt.get('target',{}).get('id')}")
        print(f"    iter={stmt.get('iter',{}).get('type')} {repr(stmt.get('iter',{}).get('id',''))[:50]}")
        print(f"    body_len={len(stmt.get('body',[]))}")
    elif stmt.get('type') == 'Try':
        print(f"    body_len={len(stmt.get('body',[]))}")
