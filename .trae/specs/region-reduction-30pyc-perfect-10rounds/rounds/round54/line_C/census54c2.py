# -*- coding: utf-8 -*-
"""R54-c census, refined: count code objects whose *ternary-kwarg call count* drops in the
recompiled product (per-call structural attribution, not whole-function KW_NAMES counts).

usage: python -X utf8 census54c2.py
"""
import importlib.util as iu
import io
import json
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r54cdiag'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')
_s = iu.spec_from_file_location('r10', REPO + r'\_r10_strict_check.py')
r10 = iu.module_from_spec(_s)
_s.loader.exec_module(r10)

_c = io.open(ROOT + r'\census54c.py', encoding='utf-8').read()
_c = _c.replace('\n\nmain()\n', '\n')
g = {'__name__': 'c54mod'}
exec(compile(_c, 'c54mod', 'exec'), g)
tc = g['ternary_kwarg_calls']

idx = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
partial = [e for e in idx
           if e.get('matched_functions') is not None and e.get('function_count') is not None
           and e['matched_functions'] < e['function_count']]
print('partial files listed in pyc_index.json: %d' % len(partial))
hits, withshape, scanned = [], 0, 0
for e in partial:
    p = e['path'].replace('\\', '/')
    prod = p[:-4] + 'OK.py'
    if not os.path.isfile(p) or not os.path.isfile(prod):
        print('SKIP missing %s' % p)
        continue
    try:
        o = r10._load_map(p)
        d = r10._load_map(py_compile.compile(prod, doraise=True, quiet=2,
                                             cfile=ROOT + r'\_cp.pyc'))
    except Exception as ex:
        print('ERR %s %r' % (p, ex))
        continue
    for name, code in o.items():
        scanned += 1
        tk = tc(code)
        n_tern = sum(1 for t in tk if t['ternary'])
        if not n_tern:
            continue
        withshape += 1
        dd = d.get(name)
        dn = sum(1 for t in tc(dd) if t['ternary']) if dd is not None else -1
        if dn < n_tern:
            hits.append((p, name, len(tk), n_tern, dn,
                         e['matched_functions'], e['function_count']))
print('code objects scanned: %d' % scanned)
print('code objects containing >=1 ternary-valued-kwarg CALL (shape present): %d' % withshape)
print('HITS -- ternary-kwarg call NOT emitted as such in the product: %d' % len(hits))
for h in hits[:15]:
    print('   %s :: %s  kw_calls=%d tern_kw=%d prod_tern_kw=%d file=%s/%s' % h)
io.open(ROOT + r'\census54c2.json', 'w', encoding='utf-8').write(
    json.dumps([{'file': h[0], 'fn': h[1], 'kw': h[2], 'tern_kw': h[3], 'prod_tern_kw': h[4],
                 'mf': h[5], 'fc': h[6]} for h in hits], ensure_ascii=False, indent=1))
