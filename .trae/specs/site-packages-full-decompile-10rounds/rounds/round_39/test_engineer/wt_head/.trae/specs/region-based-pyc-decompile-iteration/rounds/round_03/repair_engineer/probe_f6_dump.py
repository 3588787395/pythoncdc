#!/usr/bin/env python
"""Round 03 探针：dump for-else 区域结构。"""
import sys
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

SRC = "def f(items):\n    for i in items:\n        if i > 0:\n            break\n    else:\n        return None\n    return i\n"

code_obj = compile(SRC, '<f6>', 'exec')
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]
cfg = build_cfg(fn)

print('=== BLOCKS ===')
for bid, b in sorted(cfg.blocks.items()):
    ins = ', '.join(f'{i.opname}@{i.offset}' for i in b.instructions if i.opname != 'CACHE')
    succ = sorted(s.start_offset for s in b.successors)
    print(f'block {bid} [{b.start_offset}]: {ins}  -> {succ}')

g = RegionASTGenerator(cfg)
ast = g.generate()
import json
print('=== AST ===')
print(json.dumps(ast, ensure_ascii=False, default=str)[:1200])
