"""R13 trace: find where `length = len(df[df['col'] > val])` is dropped.

Instruments _build_store_statement and expr_reconstructor.reconstruct.
"""
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

# Compile
py_compile.compile(str(REPRO), doraise=True, cfile=PYC)

# Instrument before importing pycdc
import core.cfg.region_ast_generator as rag

_orig_bss = rag.RegionASTGenerator._build_store_statement
_orig_recon = None

def _traced_bss(self, instrs, block=None):
    # Detect the chained-subscr-filter pattern: contains len LOAD_GLOBAL + 2x LOAD_FAST same name + COMPARE_OP + BINARY_SUBSCR
    names = [i.argval for i in instrs if i.opname in ('LOAD_FAST', 'LOAD_GLOBAL')]
    has_len = any(i.opname == 'LOAD_GLOBAL' and i.argval == 'len' for i in instrs)
    has_compare = any(i.opname == 'COMPARE_OP' for i in instrs)
    has_two_bs = sum(1 for i in instrs if i.opname == 'BINARY_SUBSCR') >= 2
    is_target = has_len and has_compare and has_two_bs
    if is_target:
        print(f"\n[TRACE] _build_store_statement TARGET HIT")
        print(f"  instrs({len(instrs)}):")
        for i in instrs:
            print(f"    {i.opname:20s} {i.argval!r}")
    result = _orig_bss(self, instrs, block=block)
    if is_target:
        print(f"  -> result = {result}")
    return result

rag.RegionASTGenerator._build_store_statement = _traced_bss

# Instrument expr_reconstructor.reconstruct
from core.cfg import region_ast_generator as _rag_mod
# Find the expression reconstructor class
try:
    from core.cfg.code_generator import ExpressionReconstructor
    _ec_cls = ExpressionReconstructor
except Exception:
    # Search for it
    import importlib
    _ec_cls = None
    for _mod_name in ['core.cfg.code_generator', 'core.cfg.region_ast_generator']:
        try:
            _mod = importlib.import_module(_mod_name)
            for _attr in dir(_mod):
                _obj = getattr(_mod, _attr)
                if isinstance(_obj, type) and 'reconstruct' in dir(_obj) and _obj.__name__ == 'ExpressionReconstructor':
                    _ec_cls = _obj
                    break
            if _ec_cls:
                break
        except Exception:
            pass

if _ec_cls is not None:
    _orig_recon = _ec_cls.reconstruct
    def _traced_recon(self, instrs, *args, **kwargs):
        has_len = any(i.opname == 'LOAD_GLOBAL' and i.argval == 'len' for i in instrs)
        has_compare = any(i.opname == 'COMPARE_OP' for i in instrs)
        has_two_bs = sum(1 for i in instrs if i.opname == 'BINARY_SUBSCR') >= 2
        is_target = has_len and has_compare and has_two_bs
        if is_target:
            print(f"\n[TRACE] ExpressionReconstructor.reconstruct TARGET HIT")
            print(f"  instrs({len(instrs)}):")
            for i in instrs:
                print(f"    {i.opname:20s} {i.argval!r}")
        result = _orig_recon(self, instrs, *args, **kwargs)
        if is_target:
            print(f"  -> result = {result}")
        return result
    _ec_cls.reconstruct = _traced_recon
    print(f"[TRACE] instrumented {_ec_cls.__name__}.reconstruct")
else:
    print("[TRACE] ExpressionReconstructor not found - skipping reconstruct instrumentation")

# Now decompile
from pycdc import decompile_pyc
print(f"\n[TRACE] decompiling {PYC}")
src = decompile_pyc(PYC)
print(f"\n[TRACE] decompiled source:")
print(src)
