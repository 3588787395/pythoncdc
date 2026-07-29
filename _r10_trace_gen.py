#!/usr/bin/env python3
"""Trace where source_start (BoolOpRegion@286) gets generated."""
import sys, types
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, TernaryRegion

m = load_pyc_file_v2('/workspace/quotation.pyc')
c = m.code.get() if hasattr(m.code, 'get') else m.code
if hasattr(c, 'to_python_code'):
    c = c.to_python_code()

def find(co, n):
    if co.co_name == n:
        return co
    for k in co.co_consts:
        if isinstance(k, types.CodeType):
            r = find(k, n)
            if r:
                return r
    return None

f = find(c, 'load_bars_from_hundsun')
cfg = build_cfg(f)
gen = RegionASTGenerator(cfg)

# Track depth
_orig_generate_boolop = gen._generate_boolop
_orig_process_if_blocks = gen._process_if_blocks
_orig_if_generate_normal = gen._if_generate_normal
_orig_generate_region = gen._generate_region

_call_stack = []
def _indent():
    return "  " * len(_call_stack)

def _rname(r):
    if r is None:
        return "None"
    nm = type(r).__name__
    e = r.entry.start_offset if getattr(r, 'entry', None) else None
    return f"{nm}@{e}"

def _traced_generate_region(region):
    if isinstance(region, (IfRegion, BoolOpRegion, TernaryRegion)):
        e = region.entry.start_offset if getattr(region,'entry',None) else None
        if e in (0, 152, 166, 214, 286, 424, 584):
            print(f"{_indent()}>> _generate_region({_rname(region)})", flush=True)
            _call_stack.append(region)
            try:
                r = _orig_generate_region(region)
            finally:
                _call_stack.pop()
            print(f"{_indent()}<< _generate_region({_rname(region)}) -> {str(r)[:120]}", flush=True)
            return r
    return _orig_generate_region(region)

def _traced_generate_boolop(region, skip_store_targets=None):
    e = region.entry.start_offset if getattr(region,'entry',None) else None
    me = region.merge_block.start_offset if getattr(region,'merge_block',None) else None
    vt = getattr(region, 'value_target', None)
    blocks_offs = [b.start_offset for b in (getattr(region,'blocks',None) or [])]
    print(f"{_indent()}>> _generate_boolop(entry={e} merge={me} val_tgt={vt} blocks={blocks_offs})", flush=True)
    if e == 286:
        import traceback as _tb
        print("---- CALLER STACK for _generate_boolop(286) ----", flush=True)
        _tb.print_stack()
        print("---- END CALLER STACK ----", flush=True)
    r = _orig_generate_boolop(region, skip_store_targets)
    print(f"{_indent()}<< _generate_boolop(entry={e}) -> {str(r)[:200]}", flush=True)
    return r

def _traced_process_if_blocks(blocks, region, branch='then'):
    e = region.entry.start_offset if getattr(region,'entry',None) else None
    bo = [b.start_offset for b in blocks]
    if e in (0, 152, 166, 214, 584):
        print(f"{_indent()}>> _process_if_blocks(region={_rname(region)} branch={branch} blocks={bo})", flush=True)
        r = _orig_process_if_blocks(blocks, region, branch)
        print(f"{_indent()}<< _process_if_blocks(region={_rname(region)} branch={branch}) -> {str(r)[:300]}", flush=True)
        return r
    return _orig_process_if_blocks(blocks, region, branch)

def _traced_if_generate_normal(region):
    e = region.entry.start_offset if getattr(region,'entry',None) else None
    if e in (0, 152, 166, 214, 584):
        print(f"{_indent()}>> _if_generate_normal({_rname(region)})", flush=True)
        r = _orig_if_generate_normal(region)
        print(f"{_indent()}<< _if_generate_normal({_rname(region)}) -> {str(r)[:300]}", flush=True)
        return r
    return _orig_if_generate_normal(region)

gen._generate_region = _traced_generate_region
gen._generate_boolop = _traced_generate_boolop
gen._process_if_blocks = _traced_process_if_blocks
gen._if_generate_normal = _traced_if_generate_normal

ast = gen.generate()
print("\n=== TOP-LEVEL AST ===")
print(str(ast)[:600])
