# -*- coding: utf-8 -*-
"""Round 13b (shift 2) - shared runner for the minimal repros in this directory.

For every ``r13b_NN_*.py`` module in this directory:

  1. take its ``SRC`` (hand-written *corrected* source for the construct at issue),
  2. compile it to a temp ``.pyc`` **inside D:/Temp** (never next to a repo source),
  3. decompile that pyc with ``pyc_batch_verify.decompile_single`` writing the
     OK.py into the same D:/Temp directory (so no ``*OK.py`` / ``pyc_index.json``
     in the repository is touched),
  4. run the project's own strict ruler (``_r10_strict_check.check_pyc``) on the
     pyc/OK.py pair and print MATCH / MISMATCH.

MISMATCH means the minimal source reproduces the region-reduction defect.

    PYTHONIOENCODING=utf-8 python test_repros/round13b/run_all.py [name ...]
"""
import io
import os
import sys
import glob
import py_compile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
sys.path.insert(0, HERE)

TMP = os.path.join('D:' + os.sep, 'Temp', 'r13b_repro')

import _r10_strict_check as ruler  # noqa: E402  (read-only use of the ruler)
import pyc_batch_verify as pbv  # noqa: E402


def _ensure_tmp():
    if not os.path.isdir(TMP):
        os.makedirs(TMP)


def run_one(mod):
    """Compile -> decompile -> strict-compare one repro module."""
    _ensure_tmp()
    name = mod.__name__
    py = os.path.join(TMP, name + '.py')
    io.open(py, 'w', encoding='utf-8', newline='\n').write(mod.SRC)
    pyc = os.path.join(TMP, name + '.pyc')
    py_compile.compile(py, cfile=pyc, doraise=True, quiet=2)
    ok_py = os.path.join(TMP, name + 'OK.py')
    r = pbv.decompile_single(pyc, ok_py_path=ok_py)
    if not r.get('success'):
        return ('DECOMPILE-FAIL', (r.get('error') or '')[:160])
    res = ruler.check_pyc(pyc)
    if res is None:
        return ('NO-OKPY', '')
    if res.get('error'):
        return ('COMPILE-FAIL', res['error'][:160])
    if res['bad']:
        return ('MISMATCH', '%d bad / %d fn: %s' % (
            len(res['bad']), res['functions'],
            '; '.join('%s [%s] %s' % b for b in res['bad'])[:220]))
    return ('MATCH', '%d/%d functions' % (res['ok'], res['functions']))


def main(argv):
    files = sorted(glob.glob(os.path.join(HERE, 'r13b_*.py')))
    mods = []
    for f in files:
        mn = os.path.splitext(os.path.basename(f))[0]
        if argv and not any(a in mn for a in argv):
            continue
        try:
            mods.append(__import__(mn))
        except Exception as e:  # pragma: no cover
            print('%-46s IMPORT-FAIL %s' % (mn, e))
    npass = nfail = 0
    for m in mods:
        try:
            status, detail = run_one(m)
        except Exception as e:
            status, detail = 'ERROR', repr(e)[:160]
        verdict = getattr(m, 'VERDICT', '?')
        expect = getattr(m, 'EXPECT', 'MATCH')
        flag = 'OK  ' if status == expect else 'TRIP'
        if status == 'MATCH':
            npass += 1
        else:
            nfail += 1
        print('%s [%s] %-44s %-9s %s' % (flag, verdict, m.__name__, status, detail))
        if getattr(m, 'TARGET', ''):
            print('       target: %s' % m.TARGET)
        if getattr(m, 'STAGE', ''):
            print('       stage : %s' % m.STAGE)
    print('-' * 78)
    print('round13b repros: %d strict-MATCH, %d strict-MISMATCH (of %d)' % (npass, nfail, len(mods)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
