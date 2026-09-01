# -*- coding: utf-8 -*-
"""Round 04 G1: 追踪 P2 块 8 语句生成调用链。"""
import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

SRC = "def f():\n    while True:\n        i = 1\n        yield i\n"
code_obj = compile(SRC, "<p2>", "exec")
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]
cfg = build_cfg(fn)

_orig_bsfb = RegionASTGenerator._build_statements_from_instructions
_orig_gbs = RegionASTGenerator._generate_block_statements_body


def bsfb(self, instrs, *a, **k):
    r = _orig_bsfb(self, instrs, *a, **k)
    ops = [i.opname for i in instrs]
    if 'YIELD_VALUE' in ops:
        print(f"BSFB called with YIELD: ops={ops}")
        import json
        print("   result:", json.dumps(r, ensure_ascii=False, default=str)[:300])
    return r


def gbs(self, block, *a, **k):
    r = _orig_gbs(self, block, *a, **k)
    if block.start_offset == 8:
        import json
        print(f"GBS block@{block.start_offset} ops={[i.opname for i in block.instructions]}")
        print("   result:", json.dumps(r, ensure_ascii=False, default=str)[:400])
    return r


RegionASTGenerator._build_statements_from_instructions = bsfb
RegionASTGenerator._generate_block_statements_body = gbs

gen = RegionASTGenerator(cfg)
ast = gen.generate()
import json
print("\nfinal body:", json.dumps(ast.get('body', []), ensure_ascii=False, default=str)[:500])
