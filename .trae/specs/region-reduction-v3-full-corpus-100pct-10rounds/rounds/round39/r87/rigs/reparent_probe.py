"""Diagnostic: after analyze(), remove the sibling-loop break blocks from the compound
LoopRegion@232 and re-parent the sequential IfRegions to the outer loop, then regenerate.

usage: python -X utf8 work/reparent_probe.py <abs pyc> <out.py>
"""
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
sys.path.insert(0, os.path.join(MIRROR, 'core'))

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
import core.cfg.region_analyzer as ra
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

PYC, OUT = sys.argv[1], sys.argv[2]
mod = load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()

_orig_analyze = ra.RegionAnalyzer.analyze
LOG = []


def analyze(self):
    regions = _orig_analyze(self)
    loops = [r for r in regions if isinstance(r, ra.LoopRegion)]
    inner = None
    outer = None
    for r in loops:
        if r.condition_block is not None and r.entry.start_offset == 232:
            inner = r
        if r.condition_block is None and r.entry.start_offset == 232:
            outer = r
    if inner is None or outer is None:
        return regions
    sibling_blocks = set()
    for r in loops:
        if r is inner or r is outer:
            continue
        sibling_blocks.update(r.blocks)
    moved = [b for b in inner.blocks if b.start_offset in (2064, 2066, 2168)]
    for b in moved:
        inner.blocks.discard(b)
        if b in sibling_blocks:
            continue
    LOG.append('inner.break_blocks before=%s' % [b.start_offset for b in inner.break_blocks])
    inner.break_blocks = [b for b in inner.break_blocks if b.start_offset not in (2064, 2066, 2168)]
    LOG.append('inner.break_blocks after=%s' % [b.start_offset for b in inner.break_blocks])
    LOG.append('inner.children before=%s' % [(type(c).__name__, c.entry.start_offset) for c in inner.children])
    keep = []
    for c in inner.children:
        if c.entry is not None and c.entry.start_offset >= 1214 and c.entry.start_offset < 1890:
            c.parent = outer
            outer.children.append(c)
        else:
            keep.append(c)
    inner.children = keep
    LOG.append('inner.children after=%s' % [(type(c).__name__, c.entry.start_offset) for c in inner.children])
    LOG.append('outer.children after=%s' % [(type(c).__name__, c.entry.start_offset) for c in outer.children])
    for b in moved:
        if b in sibling_blocks:
            self.block_to_region[b] = None
            del self.block_to_region[b]
    return regions


ra.RegionAnalyzer.analyze = analyze

cfg = build_cfg(code)
gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
ast_dict = gen.generate()
py_ast = CFGASTConverter().convert(ast_dict)
source = CFGCodeGenerator().generate(py_ast)
open(OUT, 'w', encoding='utf-8', newline='\r\n').write(source)
print('\n'.join(LOG))
print('wrote', OUT, len(source))
