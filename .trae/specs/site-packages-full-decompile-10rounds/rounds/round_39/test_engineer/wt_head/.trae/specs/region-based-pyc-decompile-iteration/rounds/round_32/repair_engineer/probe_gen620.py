# -*- coding: utf-8 -*-
"""Instrument _generate_basic_region for the ptradeAccount function to see
what happens to the trailing return block (620)."""
import os
import sys
import marshal
import types

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"

import core.cfg.region_ast_generator as rag
from core.cfg import build_cfg


def load_code(p):
    with open(p, "rb") as f:
        f.read(16)
        return marshal.load(f)


def find(co, name):
    if (co.co_name or "<module>") == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find(c, name)
            if r:
                return r
    return None


orig = load_code(PYC)
co = find(orig, "order_response_order_update")
cfg = build_cfg(co)

_orig_basic = rag.RegionASTGenerator._generate_basic_region


def traced(self, region):
    stmts = _orig_basic(self, region)
    entry = region.entry
    offs = entry.start_offset if entry else None
    if offs == 620:
        print("=== _generate_basic_region for block 620 ===")
        print("stmts:", stmts)
        blk = next((b for b in cfg.get_blocks_in_order() if b.start_offset == 620), None)
        if blk is not None:
            print("block instrs:", [(i.opname, i.argval) for i in blk.instructions])
            role = self.region_analyzer.get_block_role(blk)
            print("block role:", role)
    return stmts


rag.RegionASTGenerator._generate_basic_region = traced

# patch _generate_region to also trace which regions get generated/skipped
_orig_gen_region = rag.RegionASTGenerator._generate_region


def traced_gen_region(self, region, **kw):
    entry = region.entry
    offs = entry.start_offset if entry else None
    if offs in (0, 4, 620):
        print(">>> _generate_region for region entry=%s type=%s" % (offs, type(region).__name__))
        print("    blocks:", sorted(b.start_offset for b in region.blocks))
        print("    all in generated:", all(b in self.generated_blocks for b in region.blocks))
    return _orig_gen_region(self, region, **kw)


rag.RegionASTGenerator._generate_region = traced_gen_region

gen = rag.RegionASTGenerator(cfg, top_level_code=None)
result = gen.generate()
print("=== generate() result type ===", type(result))
if isinstance(result, dict):
    for k in result:
        print(" key:", k, "->", type(result[k]))
        v = result[k]
        if isinstance(v, list):
            for s in v:
                print("   stmt:", s.get('type') if isinstance(s, dict) else s)
elif isinstance(result, list):
    for s in result:
        print("   stmt:", s.get('type') if isinstance(s, dict) else s)
