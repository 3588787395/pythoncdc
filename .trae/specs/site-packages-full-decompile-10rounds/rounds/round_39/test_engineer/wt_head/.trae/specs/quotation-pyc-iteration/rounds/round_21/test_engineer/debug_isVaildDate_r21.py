"""R21 调试 isVaildDate：分析区域结构，理解 return True 应在 try 内还是 post-try"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import (
    RegionASTGenerator, IfRegion, LoopRegion, TryExceptRegion,
    BoolOpRegion, MatchRegion, AssertRegion, WithRegion,
)

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

# find isVaildDate code object
target = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'isVaildDate':
        target = const
        break

print(f"isVaildDate: found={target is not None}")
if target:
    print(f"  co_varnames={target.co_varnames}")
    print(f"  co_consts={target.co_consts}")

# Build CFG
builder = CFGBuilder()
cfg = builder.build(target)

print(f"\n=== CFG blocks ===")
for bid, b in sorted(cfg.blocks.items()):
    print(f"  block {bid}:")
    for ins in b.instructions:
        print(f"    {ins.offset:4d}  {ins.opname:35s} {ins.argval!r}")
    print(f"    succs={[s.id for s in b.successors]}")

# Region analysis
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f"\n=== Regions ===")
for r in regions:
    print(f"  {type(r).__name__}: entry={r.entry.id}")
    if isinstance(r, TryExceptRegion):
        print(f"    try_blocks={[b.id for b in r.try_blocks]}")
        print(f"    handler_blocks={[(h, [b.id for b in bs]) for h, bs in r.handler_blocks] if r.handler_blocks else None}")
        print(f"    else_blocks={[b.id for b in (r.else_blocks or [])]}")
        print(f"    all blocks={[b.id for b in r.blocks]}")
        print(f"    try_blocks succs: {[(b.id, [s.id for s in b.successors]) for b in r.try_blocks]}")
        print(f"    else_blocks succs: {[(b.id, [s.id for s in b.successors]) for b in (r.else_blocks or [])]}")
    if isinstance(r, IfRegion):
        mb_id = r.merge_block.id if r.merge_block else None
        print(f"    then_blocks={[b.id for b in r.then_blocks]}")
        print(f"    else_blocks={[b.id for b in (r.else_blocks or [])]}")
        print(f"    merge_block={mb_id}")
        print(f"    entry succs={[s.id for s in r.entry.successors]}")
