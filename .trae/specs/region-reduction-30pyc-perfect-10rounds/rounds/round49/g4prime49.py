"""G4-prime (Round 43): strict ruler over every product changed by the candidate arm.

usage: python -X utf8 g4prime49.py <changed-list.txt> <arm> [a-dir]
a-side = D:/Temp/r43gate/build_head (landed bytes), b-side = D:/Temp/r43gate/build_<arm>
Per-code-object defect sets are compared; `broken` must be 0 and no CHANGED row may be a
seq_diff/target_diff that the official ruler cannot see.
"""
import importlib.util
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r43gate'
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

paths = [l.strip() for l in io.open(sys.argv[1], encoding='utf-8') if l.strip()]
ADIR = sys.argv[3] if len(sys.argv)>3 else 'build_head'
arm = sys.argv[2]


def defects(pyc, product):
    if not os.path.isfile(product):
        return {'<no-product>': 'MISSING FILE ' + product}
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


fixed = broken = changed = 0
for p in paths:
    rel = p.replace('\\', '/')
    r0 = REPO.replace('\\', '/') + '/site-packages/'
    rel = rel[len(r0):] if rel.startswith(r0) else rel
    base = rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py'
    a = defects(p, os.path.join(ROOT, ADIR, base).replace('\\', '/'))
    b = defects(p, os.path.join(ROOT, 'build_' + arm, base).replace('\\', '/'))
    print('== %s  strict-defective a=%d b=%d' % (rel, len(a), len(b)))
    for k in sorted(set(a) | set(b)):
        if k not in b:
            fixed += 1
            print('   FIXED   %s   [%s]' % (k, a[k]))
        elif k not in a:
            broken += 1
            print('   BROKEN  %s   [%s]' % (k, b[k]))
        elif a[k] != b[k]:
            changed += 1
            print('   CHANGED %s  a=[%s] b=[%s]' % (k, a[k], b[k]))
print('G4-prime affected=%d fixed=%d broken=%d changed=%d' % (len(paths), fixed, broken, changed))
