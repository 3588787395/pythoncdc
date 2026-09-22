# -*- coding: utf-8 -*-
"""Round 37 G0 driver (orchestrator-side, replaces the diagnose agent's bat_run.py).

  python -X utf8 g0_37.py <mirror_root> <battery_dir> <tag>

For every <dir>/*.py:
  1. py_compile the source  -> <dir>/pyc/<stem>.pyc          (explicit cfile, never in the repo)
  2. decompile it with the GIVEN mirror                     -> out_<tag>/<stem>.py
  3. py_compile the product -> out_<tag>/<stem>.pyc         (explicit cfile)
  4. strict-ruler compare every code object; cost = (#defective functions, sum|delta|)
  5. R36-style exception probe over the same run: hooks _generate_region (swallowed exception)
     and _generate_degraded_statements (region degradation)

Writes out_g0_<tag>.txt (one table row per case) and prints it.
"""
import glob
import importlib.util
import io
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
MIRR = os.path.abspath(sys.argv[1])
BAT = os.path.abspath(sys.argv[2])
TAG = sys.argv[3]
sys.stdout.reconfigure(encoding='utf-8')

_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

CRASH = []


def _install_probe():
    sys.path.insert(0, MIRR)
    sys.path.append(REPO)
    import pycdc
    assert os.path.dirname(os.path.abspath(pycdc.__file__)).replace('\\', '/') == MIRR.replace('\\', '/'), \
        'pycdc resolved outside the mirror: %s' % pycdc.__file__
    from core.cfg.region_ast_generator import RegionASTGenerator as G
    gen, deg = G._generate_region, G._generate_degraded_statements

    def _g(self, region, *a, **k):
        try:
            return gen(self, region, *a, **k)
        except Exception as e:
            CRASH.append('EXC:%s' % type(e).__name__)
            raise

    def _d(self, *a, **k):
        CRASH.append('DEGRADED')
        return deg(self, *a, **k)

    G._generate_region, G._generate_degraded_statements = _g, _d
    return pycdc


pycdc = _install_probe()
OUTD = os.path.join(os.path.dirname(BAT), 'out_' + TAG)
PYCD = os.path.join(BAT, 'pyc')
for d in (OUTD, PYCD):
    if not os.path.isdir(d):
        os.makedirs(d)

rows = []
for src in sorted(glob.glob(os.path.join(BAT, '*.py'))):
    stem = os.path.splitext(os.path.basename(src))[0]
    opyc = os.path.join(PYCD, stem + '.pyc')
    py_compile.compile(src, cfile=opyc, doraise=True, quiet=2)
    prod = os.path.join(OUTD, stem + '.py')
    CRASH.clear()
    try:
        io.open(prod, 'w', encoding='utf-8').write(pycdc.decompile_pyc(opyc))
    except Exception as e:
        rows.append((stem, 'DECOMPILE-FAIL', repr(e)[:60], 0, 0, ''))
        continue
    dpyc = os.path.join(OUTD, stem + '.pyc')
    try:
        py_compile.compile(prod, cfile=dpyc, doraise=True, quiet=2)
    except Exception as e:
        rows.append((stem, 'PRODUCT-COMPILE-FAIL', repr(e)[:60], 0, 0, ''))
        continue
    try:
        A, B = r10._load_map(opyc), r10._load_map(dpyc)
    except Exception as e:
        rows.append((stem, 'LOAD-FAIL', repr(e)[:60], 0, 0, ''))
        continue
    nbad, sad, detail = 0, 0, []
    for k in sorted(A):
        if k not in B:
            nbad += 1
            detail.append('%s:MISSING' % k.split('.')[-1])
            continue
        kind, msg, is_defect = r10.strict_compare(A[k], B[k])
        if not is_defect:
            continue
        nbad += 1
        d = len(r10.filtered(B[k])) - len(r10.filtered(A[k]))
        sad += abs(d)
        detail.append('%s:%s%+d' % (k.split('.')[-1], kind[:4], d))
    rows.append((stem, 'CLEAN' if not nbad else 'DEFECT', '', nbad, sad, ';'.join(detail)[:150]))
    rows[-1] = rows[-1] + ((('|probe=' + ','.join(sorted(set(CRASH)))) if CRASH else ''),)

w = max(len(r[0]) for r in rows) + 1
print('%-*s %-22s %-6s %-6s %s' % (w, 'case', 'status', 'nbad', 'sum|d|', 'detail / probe'))
for r in rows:
    print('%-*s %-22s %-6s %-6s %s' % (w, r[0], (r[1] + (' ' + r[2] if r[2] else '')), r[3], r[4],
                                       (r[5] + ' ' + (r[6] if len(r) > 6 else '')).strip()))
clean = sum(1 for r in rows if r[1] == 'CLEAN')
print('CORE=%s BAT=%s cases=%d CLEAN=%d DEFECT=%d' % (MIRR, os.path.basename(BAT), len(rows), clean,
                                                      len(rows) - clean))
