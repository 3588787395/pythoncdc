#!/usr/bin/env python3
"""Diagnose parent-child relationships for get_trading_schedule regions."""

import sys, os, marshal, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, TernaryRegion, BoolOpRegion, LoopRegion

PYC_PATH = os.path.join(HERE, 'site-packages', 'IQEngine', 'utils', 'trade_schedule.pyc')

with open(PYC_PATH, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            sub = find_code(const, name)
            if sub:
                return sub
    return None

gts = find_code(code, 'get_trading_schedule')

builder = CFGBuilder()
cfg = builder.build(gts)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("=== Region parent-child relationships ===")
for r in analyzer.regions:
    parent = r.parent
    children = r.children or []
    entry = r.entry.start_offset if r.entry else None
    parent_entry = parent.entry.start_offset if parent and parent.entry else None
    child_entries = [c.entry.start_offset if c.entry else None for c in children]
    print(f"  {type(r).__name__}@{entry}: parent={type(parent).__name__}@{parent_entry if parent else None}, children={[f'{type(c).__name__}@{e}' for c, e in zip(children, child_entries)]}")
    if isinstance(r, IfRegion):
        print(f"    then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")

print("\n=== Top-level regions ===")
# Replicate the filtering from generate()
filtered = list(analyzer.regions)
# Check which regions are top-level
for r in analyzer.regions:
    entry = r.entry.start_offset if r.entry else None
    is_toplevel = True
    for r2 in analyzer.regions:
        if r2 is r:
            continue
        if r.entry and r.entry in r2.blocks and r2 is not r:
            # Check if r is a child of r2
            if r in (r2.children or []):
                is_toplevel = False
                break
    if is_toplevel:
        print(f"  {type(r).__name__}@{entry}")
