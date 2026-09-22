"""G4-prime: strict ruler over every product changed by the candidate arm.

Compares per-code-object defect counts between the landed (a-side) and candidate (b-side)
products of each affected .pyc.  broken must be 0.
"""
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r41gate'
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

paths = [l.strip() for l in io.open(sys.argv[1], encoding='utf-8') if l.strip()]


def defects(pyc, product):
    orig = r10._load_map(pyc)
    dec = r10._compile_map(product)
    bad = {}
    for name, co in orig.items():
        dco = dec.get(name)
        if dco is None:
            bad[name] = 'MISSING'
            continue
        kind, msg, is_defect = r10.strict_compare(co, dco)
        if is_defect:
            bad[name] = '%s %s' % (kind, msg)
    for name in dec:
        if name not in orig:
            bad[name] = 'EXTRA'
    return bad


fixed = broken = 0
for p in paths:
    rel = p.replace('\\', '/')
    r0 = REPO.replace('\\', '/') + '/site-packages/'
    rel = rel[len(r0):] if rel.startswith(r0) else rel
    base = rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py'
    a = defects(p, os.path.join(ROOT, 'build_landed', base).replace('\\', '/'))
    b = defects(p, os.path.join(ROOT, 'build_r42a', base).replace('\\', '/'))
    print('== %s  strict-defective a=%d b=%d' % (rel, len(a), len(b)))
    for k in sorted(set(a) | set(b)):
        if k not in b:
            fixed += 1
            print('   FIXED   %s   [%s]' % (k, a[k]))
        elif k not in a:
            broken += 1
            print('   BROKEN  %s   [%s]' % (k, b[k]))
        elif a[k] != b[k]:
            print('   CHANGED %s  a=[%s] b=[%s]' % (k, a[k], b[k]))
print('G4-prime affected=%d fixed=%d broken=%d' % (len(paths), fixed, broken))
