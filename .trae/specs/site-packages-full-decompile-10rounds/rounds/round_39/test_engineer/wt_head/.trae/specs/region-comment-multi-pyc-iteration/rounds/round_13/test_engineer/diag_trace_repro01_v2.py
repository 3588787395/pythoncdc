"""R13 trace v2: log ALL _build_store_statement + reconstruct-with-STORE_FAST calls."""
import os
import sys
import py_compile
import marshal
import dis
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_ROOT))

REPRO = PROJECT_ROOT / '.trae/specs/region-comment-multi-pyc-iteration/rounds/round_13/test_engineer/minimal_repros/repro_01_len_chained_subscr_after_unpack.py'
PYC = str(REPRO) + 'c'
py_compile.compile(str(REPRO), doraise=True, cfile=PYC)

import core.cfg.region_ast_generator as rag

_call_counter = {'bss': 0, 'recon': 0}
_orig_bss = rag.RegionASTGenerator._build_store_statement

def _traced_bss(self, instrs, block=None):
    _call_counter['bss'] += 1
    n = _call_counter['bss']
    has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL') for i in instrs)
    if has_store:
        stores = [(i.opname, i.argval) for i in instrs if i.opname.startswith('STORE')]
        print(f"\n[BSS#{n}] _build_store_statement(instrs={len(instrs)}) stores={stores}")
        for i in instrs:
            print(f"    {i.opname:20s} {i.argval!r}")
    result = _orig_bss(self, instrs, block=block)
    if has_store:
        print(f"  -> result = {result}")
    return result

rag.RegionASTGenerator._build_store_statement = _traced_bss

from core.cfg.ast_generator_v2 import ExpressionReconstructor
_orig_recon = ExpressionReconstructor.reconstruct

def _traced_recon(self, instrs, *args, **kwargs):
    _call_counter['recon'] += 1
    n = _call_counter['recon']
    has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'UNPACK_SEQUENCE') for i in instrs)
    if has_store:
        stores = [(i.opname, i.argval) for i in instrs if i.opname.startswith('STORE') or i.opname == 'UNPACK_SEQUENCE']
        print(f"\n[RECON#{n}] reconstruct(instrs={len(instrs)}) stores/unpacks={stores}")
        for i in instrs:
            print(f"    {i.opname:20s} {i.argval!r}")
    result = _orig_recon(self, instrs, *args, **kwargs)
    if has_store:
        print(f"  -> result = {result}")
    return result

ExpressionReconstructor.reconstruct = _traced_recon

from pycdc import decompile_pyc
print(f"[TRACE] decompiling {PYC}\n")
src = decompile_pyc(PYC)
print(f"\n[TRACE] decompiled source:")
print(src)
print(f"\n[TRACE] totals: bss={_call_counter['bss']} recon={_call_counter['recon']}")
