# -*- coding: utf-8 -*-
"""Dump region ownership for order_response_order_update: where blocks 436/488/550/620 live."""
import os
import sys
import marshal
import types

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
import pycdc
from core.cfg.region_analyzer import (RegionAnalyzer, LoopRegion, TryExceptRegion,
                                      IfRegion, RegionType)
from core.cfg.cfg_builder import build_cfg

PYC = r"F:\Downloads\pythoncdc-main\site-packages\fly\simtradding\ptradeAccount.pyc"


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
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("blocks:")
for b in cfg.get_blocks_in_order():
    last = b.get_last_instruction()
    print("  %3d : %s | %s" % (b.start_offset, last.opname if last else "?",
                                last.argval if last else ""))
print()
print("block -> region:")
for b in cfg.get_blocks_in_order():
    r = analyzer.block_to_region.get(b)
    print("  %3d -> %s" % (b.start_offset, type(r).__name__ if r else "None"))

print()
print("LoopRegions:")
for r in analyzer.regions:
    if isinstance(r, LoopRegion):
        print("  Loop entry=%s header=%s back_edge=%s else=%s natural_exit=%s" % (
            r.entry.start_offset if r.entry else None,
            r.header_block.start_offset if getattr(r, 'header_block', None) else None,
            r.back_edge_block.start_offset if getattr(r, 'back_edge_block', None) else None,
            [b.start_offset for b in (r.else_blocks or [])],
            r.natural_exit.start_offset if getattr(r, 'natural_exit', None) else None))

print()
print("TryExceptRegions:")
for r in analyzer.regions:
    if isinstance(r, TryExceptRegion):
        print("  Try entry=%s try_blocks=%s except_handlers=%s handler_entry=%s else=%s finally=%s cleanup=%s has_finally=%s" % (
            r.entry.start_offset if r.entry else None,
            [b.start_offset for b in (r.try_blocks or [])],
            [[b.start_offset for b in h] for _, _, h in (r.except_handlers or [])],
            [b.start_offset for b in (r.handler_entry_blocks or [])],
            [b.start_offset for b in (r.else_blocks or [])],
            [b.start_offset for b in (r.finally_blocks or [])] if hasattr(r, 'finally_blocks') else None,
            [b.start_offset for b in (r.cleanup_blocks or [])],
            r.has_finally))

print()
print("parent/children:")
for r in analyzer.regions:
    print("  %s(%s) parent=%s" % (type(r).__name__, r.entry.start_offset if r.entry else None,
                                  type(r.parent).__name__ if getattr(r, 'parent', None) else None))
