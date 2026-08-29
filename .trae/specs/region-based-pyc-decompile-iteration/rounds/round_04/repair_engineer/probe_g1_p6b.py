# -*- coding: utf-8 -*-
"""Round 04 G1: 追踪 P6 pre-stmts 与 back_edge_stmts。"""
import sys, json
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

SRC = "def f():\n    i = 0\n    while i < 10:\n        i += 1\n        yield i\n        yield i * 2\n"
code_obj = compile(SRC, "<p6>", "exec")
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]
cfg = build_cfg(fn)

_orig_pe = RegionASTGenerator._loop_extract_pre_stmts_from_instrs


def pe(self, instrs, block):
    r = _orig_pe(self, instrs, block)
    print(f"PRE_STMTS from block@{block.start_offset}:")
    print("   ", json.dumps(r, ensure_ascii=False, default=str)[:400])
    return r


RegionASTGenerator._loop_extract_pre_stmts_from_instrs = pe

gen = RegionASTGenerator(cfg)
ast = gen.generate()
print("\nfinal body:", json.dumps(ast.get('body', []), ensure_ascii=False, default=str)[:600])
