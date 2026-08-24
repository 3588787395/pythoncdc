import sys, os, marshal, types, importlib.util, dis, tempfile
sys.path.insert(0, '.')

import core.cfg.region_ast_generator as rag

SRC = os.path.join('.trae', 'specs', 'region-comment-multi-pyc-iteration',
                   'rounds', 'round_102', 'test_engineer', 'minimal_repros',
                   'repro_102_05_const_key_map_in_try_for_if.py')
source = open(SRC, encoding='utf-8').read()
code = compile(source, SRC, 'exec')

_orig_edpv = rag.RegionASTGenerator._extract_dict_prefix_values
def edpv(self, cb):
    r = _orig_edpv(self, cb)
    print(f"[TRACE] _extract_dict_prefix_values -> {len(r)} values")
    return r
rag.RegionASTGenerator._extract_dict_prefix_values = edpv

_orig_tbcc = rag.RegionASTGenerator._try_build_ternary_chained_container
def tbcc(self, region, ternary_expr):
    r = _orig_tbcc(self, region, ternary_expr)
    print(f"[TRACE] _try_build_ternary_chained_container -> {type(r).__name__ if not isinstance(r, dict) else r.get('type')}")
    if isinstance(r, dict) and r.get('type') == 'Assign':
        v = r.get('value', {})
        print(f"        keys={ [k.get('value') for k in v.get('keys', [])] }")
    return r
rag.RegionASTGenerator._try_build_ternary_chained_container = tbcc

# trace reconstruct calls
from core.cfg.ast_generator_v2 import ExpressionReconstructor
_orig_rec = ExpressionReconstructor.reconstruct
def rec(self, instrs, **kw):
    r = _orig_rec(self, instrs, **kw)
    ops = [i.opname for i in instrs]
    if any(o == 'BUILD_CONST_KEY_MAP' for o in ops):
        print(f"[TRACE] reconstruct(BUILD_CONST_KEY_MAP in {len(instrs)} instrs, init_stack={len(kw.get('initial_stack', []))})")
        ist = kw.get('initial_stack', [])
        for n, e in enumerate(ist):
            print(f"        init_stack[{n}] = {str(e)[:120]}")
        import traceback
        tb = traceback.extract_stack()[-3:-1]
        for fr in tb:
            print(f"        called from {fr.filename.split(chr(92))[-1]}:{fr.lineno} in {fr.name}")
        if isinstance(r, dict):
            print(f"        -> {str(r)[:300]}")
    return r
ExpressionReconstructor.reconstruct = rec

import pycdc
pyc_path = tempfile.mkstemp(suffix='.pyc')[1]
with open(pyc_path, 'wb') as f:
    f.write(importlib.util.MAGIC_NUMBER + b'\x00' * 12)
    marshal.dump(code, f)
out = pycdc.decompile_pyc(pyc_path)
print("=== DECOMPILED ===")
print(out)
