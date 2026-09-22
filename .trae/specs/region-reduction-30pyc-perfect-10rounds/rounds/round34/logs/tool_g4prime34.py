# -*- coding: utf-8 -*-
"""Round 31 G4' : strict-ruler reading of every product the full-402 A/B says changed.

usage: python -X utf8 g4prime31.py <pyc> <ok.py> [<ok.py> ...]
For each (pyc, ok.py) pair print each defective function (kind + filtered lengths + real
delta) and a trailer "strict clean X/Y  sigma-defect=N  sum_abs_delta=S".
"""
import importlib.util
import sys

REPO = r'F:\Downloads\pythoncdc-main'
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
sys.stdout.reconfigure(encoding='utf-8')

pyc = sys.argv[1]
origs = r10._load_map(pyc)
for ok in sys.argv[2:]:
    decs = r10._compile_map(ok)
    nclean = sigma = 0
    total = 0
    deltas = 0
    print('--- %s  vs  %s' % (pyc.replace('\\', '/').split('/')[-1], ok.replace('\\', '/')))
    for name, o in origs.items():
        d = decs.get(name)
        if d is None:
            print('  MISSING decomp code %s' % name)
            sigma += 1
            total += 1
            continue
        total += 1
        kind, msg, is_defect = r10.strict_compare(o, d)
        fo, fd = r10.filtered(o), r10.filtered(d)
        deltas += abs(len(fo) - len(fd))
        if is_defect:
            sigma += 1
            print('  DEFECT %-58s [%s] %s  orig=%d decomp=%d delta=%+d'
                  % (name, kind, msg, len(fo), len(fd), len(fd) - len(fo)))
        else:
            nclean += 1
    print('  strict clean %d/%d  sigma-defect=%d  sum_abs_delta=%d'
          % (nclean, total, sigma, deltas))
