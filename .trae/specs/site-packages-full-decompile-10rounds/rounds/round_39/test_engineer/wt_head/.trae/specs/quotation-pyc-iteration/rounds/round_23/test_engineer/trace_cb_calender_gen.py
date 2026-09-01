"""R23-N9 跟踪 get_cb_calender_info 的 LoopRegion body 生成"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, LoopRegion, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

import types
target = None
for const in code_obj.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'get_cb_calender_info':
        target = const
        break

builder = CFGBuilder()
cfg = builder.build(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find the top-level LoopRegion
top_loop = None
for r in analyzer.regions:
    if isinstance(r, LoopRegion) and r.parent is None and r.entry and r.entry.start_offset == 492:
        top_loop = r
        break

print(f"Top LoopRegion: entry={top_loop.entry.start_offset}")
print(f"  blocks: {sorted(b.start_offset for b in top_loop.blocks)}")
print(f"  body_blocks: {[b.start_offset for b in top_loop.body_blocks]}")
print(f"  header_block: {top_loop.header_block.start_offset}")

# Check children
print(f"\n  Children:")
for child in sorted([r for r in analyzer.regions if r.parent is top_loop], key=lambda r: r.entry.start_offset if r.entry else 0):
    print(f"    {type(child).__name__} entry={child.entry.start_offset if child.entry else None}")

# Check if block 1120 is in body_blocks
block_1120 = cfg.blocks.get(1120)
print(f"\n  Block@1120 in body_blocks: {block_1120 in top_loop.body_blocks}")
print(f"  Block@1120 in blocks: {block_1120 in top_loop.blocks}")

# Now generate and trace
generator = RegionASTGenerator(cfg, analyzer, target)

# Patch _generate_block_statements to trace block 1120
orig_gbs = generator._generate_block_statements
def traced_gbs(block, *args, **kwargs):
    if block.start_offset == 1120:
        import traceback
        print(f"\n>>> _generate_block_statements(block@{block.start_offset})")
        traceback.print_stack(limit=10)
    return orig_gbs(block, *args, **kwargs)
generator._generate_block_statements = traced_gbs

# Patch _generate_try to trace
orig_gt = generator._generate_try
def traced_gt(region, *args, **kwargs):
    if region.entry and region.entry.start_offset == 1138:
        print(f"\n>>> _generate_try(entry={region.entry.start_offset})")
    return orig_gt(region, *args, **kwargs)
generator._generate_try = traced_gt

result = generator.generate()

# Show the relevant part of the generated AST
stmts = result.get('body', result) if isinstance(result, dict) else result
if isinstance(stmts, dict) and 'body' in stmts:
    stmts = stmts['body']

# Find the for loop
for i, stmt in enumerate(stmts):
    if stmt.get('type') == 'For':
        print(f"\n=== For loop at index {i} ===")
        body = stmt.get('body', [])
        for j, s in enumerate(body):
            t = s.get('type')
            if t == 'Try':
                print(f"  [{j}] Try")
                # Show what's inside the try
                try_body = s.get('body', [])
                for k, ts in enumerate(try_body[:3]):
                    print(f"      try_body[{k}]: {ts.get('type')}")
                handlers = s.get('handlers', [])
                for h in handlers:
                    print(f"      handler body: {len(h.get('body', []))} stmts")
                # Show what's after the try in the for body
                if j + 1 < len(body):
                    print(f"  [{j+1}] {body[j+1].get('type')} (AFTER try)")
            elif t == 'Assign':
                targets = s.get('targets', [])
                tname = targets[0].get('id') if targets and targets[0].get('type') == 'Name' else '?'
                v = s.get('value', {})
                print(f"  [{j}] Assign {tname} = {v.get('type')}")
            elif t == 'Expr':
                v = s.get('value', {})
                print(f"  [{j}] Expr {v.get('type')}")
            else:
                print(f"  [{j}] {t}")
        break
