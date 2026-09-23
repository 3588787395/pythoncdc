# -*- coding: utf-8 -*-
"""G4-prime (Round 51): official-MOVED files re-checked on the strict ruler, head vs landed.

For every path whose official product sha moved in G4, decompile-free: reuse the
already-built products under build_head / build_landed and run strict_compare
per code object, then tally FIXED / BROKEN / CHANGED.
"""
import importlib.util
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r51sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)


def load(p):
    d = {}
    for l in io.open(p, encoding='utf-8'):
        if l.strip():
            r = json.loads(l)
            d[r['path'].replace(chr(92), '/')] = r
    return d


H = load('D:/Temp/r51b/g4_head.jsonl')
C = load('D:/Temp/r51b/g4_cand.jsonl')
moved = [k for k in sorted(H) if H[k]['sha'] != C[k]['sha']]
print('official-MOVED files: %d' % len(moved))


def strict(prod, pyc):
    o = r10._load_map(pyc)
    d = r10._compile_map(prod)
    out = {}
    for name in sorted(set(o) & set(d)):
        kind, msg, isdef = r10.strict_compare(o[name], d[name])
        out[name] = (kind, msg) if isdef else None
    for name in sorted(set(o) - set(d)):
        out[name] = ('missing', name)
    return out


tf = tb = tc = 0
for k in moved:
    rel = k.split('site-packages/')[-1]
    fn = rel.replace('/', '__')[:-4] + 'OK.py'
    ph = 'D:/Temp/r51b/build_head/' + fn
    pl = 'D:/Temp/r51b/build_landed/' + fn
    if not (os.path.exists(ph) and os.path.exists(pl)):
        print('  %-58s NO-PRODUCT head=%s landed=%s' % (rel[-58:], os.path.exists(ph), os.path.exists(pl)))
        continue
    a = strict(ph, k.replace('/', os.sep))
    b = strict(pl, k.replace('/', os.sep))
    for name in sorted(set(a) | set(b)):
        x, y = a.get(name), b.get(name)
        if x == y:
            continue
        tc += 1
        if x and not y:
            tf += 1
            print('  FIXED   %-58s %s %s' % (rel[-58:], name.split('.')[-1][:30], x))
        elif y and not x:
            tb += 1
            print('  BROKEN  %-58s %s %s' % (rel[-58:], name.split('.')[-1][:30], y))
        else:
            print('  CHANGED %-58s %s %s -> %s' % (rel[-58:], name.split('.')[-1][:30], x, y))
print('affected=%d fixed=%d broken=%d changed=%d' % (tc, tf, tb, tc - tf - tb))
