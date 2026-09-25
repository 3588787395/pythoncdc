# -*- coding: utf-8 -*-
"""G4' strict ruler over the REAL repo products (site-packages/**/<name>OK.py).

  python -X utf8 strict_repo65.py <list.txt> [<out.json>]

Unlike cstrict65.py (which reads harness build_<arm> products) this walks the committed
products, i.e. exactly what the round ships. Also hashes each product against the mirror
product of the same name when one exists, so 'the shipped bytes == the measured bytes' is
proven per file rather than assumed.
"""
import hashlib
import io
import json
import os
import sys

sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
import _r10_strict_check as S  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
GATE = r'D:/Temp/opencode/r65gate'
paths = [l.strip() for l in io.open(sys.argv[1], encoding='utf-8') if l.strip()]
out = sys.argv[2] if len(sys.argv) > 2 else ''
res = []
for p in paths:
    rel = p.split('site-packages/')[-1]
    prod = os.path.join(REPO, 'site-packages', rel.replace('.pyc', 'OK.py'))
    mirror = os.path.join(GATE, 'build_m65',
                          rel.replace('/', '__').replace('.pyc', '') + 'OK.py')
    tag = ''
    if os.path.isfile(mirror):
        ha = hashlib.sha256(io.open(prod, 'rb').read()).hexdigest()[:16]
        hb = hashlib.sha256(io.open(mirror, 'rb').read()).hexdigest()[:16]
        tag = 'mirror-sha %s%s' % (ha[:8], '=measured' if ha == hb else '!=measured(' + hb[:8] + ')')
    if not os.path.isfile(prod):
        res.append({'pyc': p, 'error': 'no product'})
        print('%-58s NO-PRODUCT' % rel)
        continue
    origs = S._load_map(p.replace('/', os.sep))
    try:
        decs = S._compile_map(prod)
    except Exception as e:
        res.append({'pyc': p, 'error': 'compile failed %s' % e})
        print('%-58s COMPILE-FAIL %s' % (rel, e))
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
    print('%-58s strict %d/%d  missing=%d extra=%d  %s' %
          (rel, ok, len(names), len(missing), len(extra), tag))
    for b in bad:
        print('      %-46s [%s] %s' % (b[0].split('.')[-1][:46], b[1], b[2][:90]))
    for m in missing:
        print('      MISSING nested code object: %s' % m)
    for m in extra:
        print('      EXTRA   nested code object: %s' % m)
    res.append({'pyc': p, 'product': prod.replace('\\', '/'), 'functions': len(names),
                'ok': ok, 'bad': bad, 'missing': missing, 'extra': extra})
if out:
    io.open(out, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
print('STRICT TOTAL ok=%d / functions=%d' % (sum(r['ok'] for r in res if 'ok' in r),
                                             sum(r['functions'] for r in res if 'functions' in r)))
