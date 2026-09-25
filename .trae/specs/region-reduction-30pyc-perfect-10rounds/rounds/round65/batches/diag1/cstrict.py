# -*- coding: utf-8 -*-
"""Center-side STRICT ruler over products written by h62.py under build_<arm>.

  python -X utf8 cstrict.py <build_dir_name> <list.txt> [<out.json>]

Pairs each pyc with the harness product in the build dir and reports, per file,
strict ok/functions and every defect [name, kind, message], plus missing/extra
nested code objects (a code object the product never emits shows up as `missing`,
which the official ruler cannot see).
"""
import io
import json
import os
import sys

sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
import _r10_strict_check as S  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
GATE = r'D:/Temp/opencode/r65gate/diag1'

build = os.path.join(GATE, sys.argv[1])
paths = [l.strip() for l in io.open(sys.argv[2], encoding='utf-8') if l.strip()]
out = sys.argv[3] if len(sys.argv) > 3 else ''
res = []
for p in paths:
    rel = p.split('site-packages/')[-1]
    prod = os.path.join(build, rel.replace('/', '__').replace('.pyc', '') + 'OK.py')
    if not os.path.isfile(prod):
        res.append({'pyc': p, 'error': 'no product %s' % os.path.basename(prod)})
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
    print('%-58s strict %d/%d  missing=%d extra=%d' % (rel, ok, len(names), len(missing), len(extra)))
    for b in bad:
        print('      %-46s [%s] %s' % (b[0][:46], b[1], b[2][:90]))
    for m in missing:
        print('      MISSING nested code object: %s' % m)
    for m in extra:
        print('      EXTRA   nested code object: %s' % m)
    res.append({'pyc': p, 'product': prod.replace('\\', '/'), 'functions': len(names),
                'ok': ok, 'bad': bad, 'missing': missing, 'extra': extra})
if out:
    io.open(out, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
    print('wrote', out)
