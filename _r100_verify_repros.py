#!/usr/bin/env python3
"""R100 verify repros"""
import sys, os, marshal, types, tempfile
sys.path.insert(0, '.')
import pycdc
from testqouter.round1.base import compare_bytecode

REPRO_DIR = '.trae/specs/region-comment-multi-pyc-iteration/rounds/round_100/test_engineer/minimal_repros'

def verify_repro(py_path):
    orig_code = compile(open(py_path, encoding='utf-8').read(), py_path, 'exec')
    with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False) as f:
        import importlib.util
        f.write(importlib.util.MAGIC_NUMBER + b'\x00' * 12)
        marshal.dump(orig_code, f)
        pyc_path = f.name
    try:
        decompiled = pycdc.decompile_pyc(pyc_path)
        decomp_code = compile(decompiled, '<decomp>', 'exec')
        result = compare_bytecode(orig_code, decomp_code)
        # [R100 fix] compare_bytecode 契约：返回非空 dict，
        # match=True 当且仅当 true_diffs 为空（jump_only 亦视为语义等价）。
        def _is_match(r):
            if r is None:
                return True
            if isinstance(r, dict):
                if r.get('match') or r.get('jump_only'):
                    return True
                return len(r.get('true_diffs', [])) == 0
            return False
        all_match = _is_match(result)
        orig_funcs = [c for c in orig_code.co_consts if isinstance(c, types.CodeType)]
        decomp_funcs = [c for c in decomp_code.co_consts if isinstance(c, types.CodeType)]
        if all_match and len(orig_funcs) == len(decomp_funcs):
            for of, df in zip(orig_funcs, decomp_funcs):
                r = compare_bytecode(of, df)
                if not _is_match(r):
                    all_match = False
                    break
        status = 'MATCH' if all_match else 'DEFECT-REPRO'
        print('  %s: %s' % (os.path.basename(py_path), status))
        return status
    except Exception as e:
        print('  %s: ERROR - %s' % (os.path.basename(py_path), e))
        return 'ERROR'
    finally:
        os.unlink(pyc_path)

print('=== R100 repros ===')
files = sorted([f for f in os.listdir(REPRO_DIR) if f.endswith('.py')])
for f in files:
    verify_repro(os.path.join(REPRO_DIR, f))
