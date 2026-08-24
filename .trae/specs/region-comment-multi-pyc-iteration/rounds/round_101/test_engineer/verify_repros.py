#!/usr/bin/env python3
"""R101 verify repros.

For every minimal_repros/repro_101_*.py:
  1. compile source to a header-pyc (importlib MAGIC + zero header) via marshal
  2. decompile with pycdc.decompile_pyc
  3. recompile and compare per-function bytecode (compare_bytecode)
Classifies: DEFECT-REPRO / MATCH / ERROR, printing first diff for defects.
"""
import sys, os, marshal, types, tempfile, importlib.util
sys.path.insert(0, '.')
import pycdc
from testqouter.round1.base import compare_bytecode

REPRO_DIR = os.path.join(
    '.trae', 'specs', 'region-comment-multi-pyc-iteration', 'rounds',
    'round_101', 'test_engineer', 'minimal_repros')


def _is_match(r):
    if r is None:
        return True
    if isinstance(r, dict):
        if r.get('match') or r.get('jump_only'):
            return True
        return len(r.get('true_diffs', [])) == 0
    return False


def _funcs(code):
    out = {}

    def walk(c):
        out[c.co_name or '<module>'] = c
        for k in c.co_consts:
            if isinstance(k, types.CodeType):
                walk(k)
    walk(code)
    return out


def compile_to_pyc(source, py_path):
    orig_code = compile(source, py_path, 'exec')
    fd, pyc_path = tempfile.mkstemp(suffix='.pyc')
    with os.fdopen(fd, 'wb') as f:
        f.write(importlib.util.MAGIC_NUMBER + b'\x00' * 12)
        marshal.dump(orig_code, f)
    return pyc_path, orig_code


def verify_repro(py_path):
    source = open(py_path, encoding='utf-8').read()
    pyc_path, orig_code = compile_to_pyc(source, py_path)
    try:
        decompiled = pycdc.decompile_pyc(pyc_path)
        decomp_code = compile(decompiled, '<decomp>', 'exec')
        om, dm = _funcs(orig_code), _funcs(decomp_code)
        defects = []
        if set(om) != set(dm):
            defects.append(('names', sorted(set(om) ^ set(dm))))
        for name in sorted(set(om) & set(dm)):
            r = compare_bytecode(om[name], dm[name])
            if not _is_match(r):
                d = r['true_diffs'][0] if r.get('true_diffs') else \
                    r.get('jump_diffs', [{}])[0]
                defects.append((name, len(r.get('true_diffs', [])), d))
        status = 'DEFECT-REPRO' if defects else 'MATCH'
        print(f'  {os.path.basename(py_path)}: {status}')
        for dft in defects:
            print(f'      -> {dft}')
        return status
    except Exception as e:
        print(f'  {os.path.basename(py_path)}: ERROR - {e}')
        return 'ERROR'
    finally:
        os.unlink(pyc_path)


if __name__ == '__main__':
    print('=== R101 repros ===')
    files = sorted(f for f in os.listdir(REPRO_DIR)
                   if f.startswith('repro_101_') and f.endswith('.py'))
    tally = {}
    for f in files:
        st = verify_repro(os.path.join(REPRO_DIR, f))
        tally[st] = tally.get(st, 0) + 1
    print('=== summary ===')
    for k in sorted(tally):
        print(f'  {k}: {tally[k]}')
