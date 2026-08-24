import sys, os, marshal, types, importlib.util, dis, tempfile
sys.path.insert(0, '.')
sys.path.insert(0, r'.trae\specs\region-comment-multi-pyc-iteration\rounds\round_102\test_engineer')

import core.cfg.region_ast_generator as rag

SRC = os.path.join('.trae', 'specs', 'region-comment-multi-pyc-iteration',
                   'rounds', 'round_102', 'test_engineer', 'minimal_repros',
                   'repro_102_06_subscript_augassign_rich_branches.py')
source = open(SRC, encoding='utf-8').read()
code = compile(source, SRC, 'exec')

# Instrument: log calls to _build_subscript_assign and _split_subscr_operands
_orig_bsa = rag.RegionASTGenerator._build_subscript_assign
_orig_sso = rag.RegionASTGenerator._split_subscr_operands
_orig_bes = rag.RegionASTGenerator._build_effective_stmts

def bsa(self, instrs):
    r = _orig_bsa(self, instrs)
    print(f"[TRACE] _build_subscript_assign({len(instrs)} instrs) -> {r.get('type') if isinstance(r, dict) else r}")
    return r

def sso(self, expr_instrs):
    r = _orig_sso(self, expr_instrs)
    print(f"[TRACE] _split_subscr_operands({len(expr_instrs)} instrs) -> {'ok' if r else None}")
    return r

def bes(self, block, effective):
    ops = [i.opname for i in effective]
    print(f"[TRACE] _build_effective_stmts(block off={getattr(block, 'start_offset', '?')}) ops={ops}")
    r = _orig_bes(self, block, effective)
    for s in r:
        print(f"        -> stmt {str(s)[:150]}")
    return r

rag.RegionASTGenerator._build_subscript_assign = bsa
rag.RegionASTGenerator._split_subscr_operands = sso
rag.RegionASTGenerator._build_effective_stmts = bes

import pycdc
pyc_path = tempfile.mkstemp(suffix='.pyc')[1]
with open(pyc_path, 'wb') as f:
    f.write(importlib.util.MAGIC_NUMBER + b'\x00' * 12)
    marshal.dump(code, f)
out = pycdc.decompile_pyc(pyc_path)
print("=== DECOMPILED ===")
print(out)
