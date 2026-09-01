# -*- coding: utf-8 -*-
"""Round 04 G1: 全面插桩 P6 分发路径。"""
import sys, json
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

SRC = "def f():\n    i = 0\n    while i < 10:\n        i += 1\n        yield i\n        yield i * 2\n"
code_obj = compile(SRC, "<p6>", "exec")
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]
cfg = build_cfg(fn)

_orig_nbe = RegionASTGenerator._loop_process_natural_back_edge
_orig_gbsb = RegionASTGenerator._generate_block_statements_body
_orig_db = RegionASTGenerator._loop_dispatch_block
_orig_pe = RegionASTGenerator._loop_extract_pre_stmts_from_instrs
_orig_be = RegionASTGenerator._loop_handle_back_edge


def nbe(self, block, back_edge_stmts, back_edge_source_blocks=None):
    r = _orig_nbe(self, block, back_edge_stmts, back_edge_source_blocks)
    print(f"NBE block@{block.start_offset} -> {r}, stmts={json.dumps(back_edge_stmts, ensure_ascii=False, default=str)[:200]}")
    return r


def gbsb(self, block, *a, **k):
    r = _orig_gbsb(self, block, *a, **k)
    print(f"GBSB block@{block.start_offset} -> {json.dumps(r, ensure_ascii=False, default=str)[:200]}")
    return r


def db(self, block, region, *a, **k):
    print(f"DISPATCH block@{block.start_offset} (region entry={region.entry.start_offset})")
    r = _orig_db(self, block, region, *a, **k)
    print(f"   -> handled={r}")
    return r


def pe(self, instrs, block):
    r = _orig_pe(self, instrs, block)
    print(f"PE block@{block.start_offset} -> {json.dumps(r, ensure_ascii=False, default=str)[:300]}")
    return r


def be(self, block, region, *a, **k):
    print(f"HANDLE_BE block@{block.start_offset}")
    return _orig_be(self, block, region, *a, **k)


RegionASTGenerator._loop_process_natural_back_edge = nbe
RegionASTGenerator._generate_block_statements_body = gbsb
RegionASTGenerator._loop_dispatch_block = db
RegionASTGenerator._loop_extract_pre_stmts_from_instrs = pe
RegionASTGenerator._loop_handle_back_edge = be

gen = RegionASTGenerator(cfg)
ast = gen.generate()
print("\nfinal while body:", json.dumps([s for s in ast.get('body', []) if s.get('type') == 'While'][0].get('body', []), ensure_ascii=False, default=str)[:300])
