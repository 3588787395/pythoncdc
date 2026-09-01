#!/usr/bin/env python3
"""R100 regression: compile->decompile->compare_bytecode for prior round repros"""
import sys, os, marshal, tempfile, importlib.util, types
sys.path.insert(0, '.')
import pycdc
from testqouter.round1.base import compare_bytecode

def _is_match(r):
    if r is None:
        return True
    if isinstance(r, dict):
        if r.get('match') or r.get('jump_only'):
            return True
        return len(r.get('true_diffs', [])) == 0
    return False

def verify(py_path):
    try:
        orig_code = compile(open(py_path, encoding='utf-8').read(), py_path, 'exec')
    except Exception as e:
        return 'COMPILE-ERR:%s' % e
    with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False) as f:
        f.write(importlib.util.MAGIC_NUMBER + b'\x00' * 12)
        marshal.dump(orig_code, f)
        pyc_path = f.name
    try:
        decompiled = pycdc.decompile_pyc(pyc_path)
        decomp_code = compile(decompiled, '<decomp>', 'exec')
        ok = _is_match(compare_bytecode(orig_code, decomp_code))
        if not ok:
            return 'DEFECT'
        orig_funcs = [c for c in orig_code.co_consts if isinstance(c, types.CodeType)]
        decomp_funcs = [c for c in decomp_code.co_consts if isinstance(c, types.CodeType)]
        if len(orig_funcs) != len(decomp_funcs):
            return 'DEFECT(fncount %d!=%d)' % (len(orig_funcs), len(decomp_funcs))
        for of, df in zip(orig_funcs, decomp_funcs):
            if not _is_match(compare_bytecode(of, df)):
                return 'DEFECT(inner)'
        # recurse nested code objects one more level
        of2 = [c for c in sum([[d for d in f.co_consts if isinstance(d, types.CodeType)] for f in orig_funcs], [])]
        df2 = [c for c in sum([[d for d in g.co_consts if isinstance(d, types.CodeType)] for g in decomp_funcs], [])]
        for of, df in zip(of2, df2):
            if not _is_match(compare_bytecode(of, df)):
                return 'DEFECT(nested)'
        return 'MATCH'
    except Exception as e:
        return 'ERROR:%s' % e
    finally:
        os.unlink(pyc_path)

total = match = 0
defects = []
for base in sys.argv[1:]:
    for root, dirs, files in os.walk(base):
        for fn in sorted(files):
            if not fn.endswith('.py'):
                continue
            p = os.path.join(root, fn)
            st = verify(p)
            total += 1
            if st == 'MATCH':
                match += 1
            else:
                defects.append((p, st))
            print('%s: %s' % (os.path.relpath(p, base), st))
print('=== total=%d match=%d defect=%d ===' % (total, match, len(defects)))
for p, st in defects:
    print('DEFECT:', p, st)
