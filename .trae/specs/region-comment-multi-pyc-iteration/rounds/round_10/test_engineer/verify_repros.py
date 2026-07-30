"""Verify all R10 minimal repros: compile, decompile, recompile, bytecode diff.

For each repro_NN_*.py:
  1. py_compile source -> .pyc (original)
  2. decompile via pycdc -> decompiled source
  3. py_compile decompiled -> recompiled .pyc
  4. compare bytecode (original vs recompiled)

A repro is DEFECT-REPRO if:
  - decompile raises an exception, OR
  - the decompiled source has a SyntaxError when recompiled, OR
  - the bytecode of the recompiled source differs from the original.

Pattern Q specifically: the decompiled f-string has a quote conflict
(single-quoted Constant string inside single-quoted f-string) -> SyntaxError.
"""
import os
import sys
import py_compile
import marshal
import types
import glob

sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc  # noqa: E402
from testqouter.round1.base import compare_bytecode  # noqa: E402

REPRO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'minimal_repros')
if not os.path.isdir(REPRO_DIR):
    REPRO_DIR = os.path.dirname(os.path.abspath(__file__))


def load_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def extract(code):
    out = {code.co_name or '<module>': code}
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            out.update(extract(c))
    return out


def main():
    repros = sorted(glob.glob(os.path.join(REPRO_DIR, 'repro_*.py')))
    print('Found ' + str(len(repros)) + ' repros')
    defects = []
    for rp in repros:
        name = os.path.basename(rp)
        # Step 1: compile source to pyc
        orig_pyc = rp + 'c'
        try:
            py_compile.compile(rp, orig_pyc, doraise=True, quiet=0)
        except py_compile.PyCompileError as e:
            print('  ' + name + ': SOURCE COMPILE ERROR ' + str(e))
            continue
        # Step 2: decompile
        try:
            decomp = decompile_pyc(orig_pyc)
        except Exception as e:
            print('  ' + name + ': DECOMPILE ERROR ' + type(e).__name__ + ': ' + str(e))
            defects.append((name, 'decompile-error'))
            try:
                os.remove(orig_pyc)
            except OSError:
                pass
            continue
        # Step 3: recompile decompiled source
        decomp_py = rp + '.decomp.py'
        with open(decomp_py, 'w', encoding='utf-8') as f:
            f.write(decomp)
        try:
            py_compile.compile(decomp_py, doraise=True, quiet=0)
        except py_compile.PyCompileError as e:
            print('  ' + name + ': RECOMPILE SYNTAX ERROR ' + str(e).splitlines()[0])
            defects.append((name, 'syntax-error'))
            try:
                os.remove(orig_pyc)
            except OSError:
                pass
            try:
                os.remove(decomp_py)
            except OSError:
                pass
            try:
                os.remove(decomp_py + 'c')
            except OSError:
                pass
            continue
        except SyntaxError as e:
            print('  ' + name + ': RECOMPILE SYNTAX ERROR ' + str(e))
            defects.append((name, 'syntax-error'))
            try:
                os.remove(orig_pyc)
            except OSError:
                pass
            try:
                os.remove(decomp_py)
            except OSError:
                pass
            try:
                os.remove(decomp_py + 'c')
            except OSError:
                pass
            continue
        # Step 4: bytecode diff
        # py_compile writes to __pycache__; find the cfile
        cfile = py_compile.compile(decomp_py, doraise=True, quiet=0)
        orig_code = load_code(orig_pyc)
        decomp_code = load_code(cfile)
        orig_map = extract(orig_code)
        decomp_map = extract(decomp_code)
        common = set(orig_map) & set(decomp_map)
        mismatch = []
        for n in sorted(common):
            cmp = compare_bytecode(orig_map[n], decomp_map[n])
            if not cmp.get('match'):
                mismatch.append(n)
        if mismatch:
            print('  ' + name + ': BYTECODE MISMATCH ' + str(mismatch))
            defects.append((name, 'bytecode-mismatch:' + ','.join(mismatch)))
        else:
            print('  ' + name + ': OK')
        # Cleanup
        for p in (orig_pyc, decomp_py, decomp_py + 'c', cfile):
            try:
                os.remove(p)
            except OSError:
                pass
    print('\nTotal: ' + str(len(repros)) + ' repros, ' + str(len(defects)) + ' DEFECT-REPROs')
    for d in defects:
        print('  DEFECT: ' + d[0] + ' reason=' + d[1])
    return 0 if not defects else 1


if __name__ == '__main__':
    sys.exit(main())
