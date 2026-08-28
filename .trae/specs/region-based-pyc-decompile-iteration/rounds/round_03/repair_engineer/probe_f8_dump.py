#!/usr/bin/env python
"""Round 03 修复工程师探针：dump P9 的区域树，定位 if 体语句重排根因。"""
import sys
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
import dis
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

SRC = "def f(engine):\n    if engine.a:\n        if engine.b:\n            engine.c()\n        engine.a = engine.a or 10\n"

code_obj = compile(SRC, '<p9>', 'exec')
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]
cfg = build_cfg(fn)

print('=== BLOCKS ===')
for bid, b in sorted(cfg.blocks.items()):
    ins = ', '.join(f'{i.opname}@{i.offset}' for i in b.instructions
                    if i.opname not in ('CACHE',))
    print(f'block {bid} [{b.start_offset}]: {ins}')
print('=== SUCCS ===')
for bid, b in sorted(cfg.blocks.items()):
    print(f'  {bid} -> {b.successors}')

gen = RegionASTGenerator(cfg)
ast_dict = gen.generate()

print('=== REGION TREE (gen.region_tree or similar) ===')
attrs = [a for a in dir(gen) if 'region' in a.lower()]
print('gen attrs:', attrs[:30])

ra = gen.region_analyzer
print('=== ra attrs ===')
print([a for a in dir(ra) if not a.startswith('__')][:60])

regs = getattr(ra, 'regions', None)
print('=== regions ===', type(regs))
if regs is not None:
    items = regs.items() if isinstance(regs, dict) else enumerate(regs)
    for k, r in items:
        blocks = getattr(r, "blocks", []) or []
        bl = sorted(getattr(b, 'start_offset', -1) for b in blocks)
        print(f'-- region {k}: type={getattr(r,"region_type",None)} '
              f'entry={getattr(getattr(r,"entry_block",None),"start_offset",None)} '
              f'blocks={bl} '
              f'merge={getattr(getattr(r,"merge_block",None),"start_offset",None)}')
b2r = getattr(ra, 'block_to_region', None)
if b2r is not None:
    print('=== block_to_region ===')
    for bid, r in sorted(b2r.items(), key=lambda kv: str(kv[0])):
        print(f'  block {bid} -> region {getattr(r, "region_type", r)} '
              f'entry={getattr(r, "entry_block", None)}')
