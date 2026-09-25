# -*- coding: utf-8 -*-
"""Centre-side STRICT ruler for products written by h62.py, including scratch repros.

  python -X utf8 sstrict67.py <build_dir_name> <list.txt> [<out.json>]

`cstrict.py` only knows how to pair files that live under `site-packages/`; synthetic
repros live in test_repros/ or in an agent workspace, so this variant derives the product
name with exactly h62.py's rule (strip the repo site-packages prefix if present, then
'/'->'__', ':'->'_', '.pyc'->'' , + 'OK.py' inside build_<arm>/).
"""
import io
import json
import os
import sys

sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
import _r10_strict_check as S  # noqa: E402

REPO = r'F:/Downloads/pythoncdc-main'
GATE = r'D:/Temp/opencode/r70gate/center'
sys.stdout.reconfigure(encoding='utf-8')

build = os.path.join(GATE, sys.argv[1])
paths = [l.strip() for l in io.open(sys.argv[2], encoding='utf-8') if l.strip()]
out = sys.argv[3] if len(sys.argv) > 3 else ''
res = []
for p in paths:
    rel = p.replace('\\', '/')
    pre = REPO + '/site-packages/'
    if rel.startswith(pre):
        rel = rel[len(pre):]
    prod = os.path.join(build, rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py')
    if not os.path.isfile(prod):
        res.append({'pyc': p, 'error': 'no product %s' % os.path.basename(prod)})
        print('%-70s NO-PRODUCT' % os.path.basename(p))
        continue
    origs = S._load_map(p.replace('/', os.sep))
    try:
        decs = S._compile_map(prod)
    except Exception as e:
        res.append({'pyc': p, 'error': 'compile failed %s' % e})
        print('%-70s COMPILE-FAIL %s' % (os.path.basename(p), e))
        continue
    names = sorted(set(origs) & set(decs))
    ok, bad = 0, []
    for n in names:
        kind, msg, _ = S.strict_compare(origs[n], decs[n])
        if kind is None:
            ok += 1
        else:
            bad.append([n, kind, msg])
    missing = sorted(set(origs) - set(decs))
    extra = sorted(set(decs) - set(origs))
    print('%-70s strict %d/%d  missing=%d extra=%d' % (os.path.basename(p), ok, len(names),
                                                       len(missing), len(extra)))
    for b in bad:
        print('      %-46s [%s] %s' % (b[0].split('.')[-1][:46], b[1], b[2][:110]))
    res.append({'pyc': p, 'product': prod.replace('\\', '/'), 'functions': len(names),
                'ok': ok, 'bad': bad, 'missing': missing, 'extra': extra})
print('STRICT TOTAL ok=%d / functions=%d / defects=%d' %
      (sum(r.get('ok', 0) for r in res), sum(r.get('functions', 0) for r in res),
       sum(len(r.get('bad') or []) for r in res)))
if out:
    io.open(out, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
