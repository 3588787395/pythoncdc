# -*- coding: utf-8 -*-
"""diag4 r67: STRICT ruler for arbitrary scratch pyc paths (cstrict.py only resolves
site-packages/ names). Products are named exactly as h62.py run writes them.
usage: python -X utf8 sstrict.py <build_dir_name> <list.txt>
"""
import io
import json
import os
import sys

sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
import _r10_strict_check as S  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')
GATE = r'D:/Temp/opencode/r67gate/diag4'
REPO = r'F:/Downloads/pythoncdc-main'
build = os.path.join(GATE, sys.argv[1])
paths = [l.strip() for l in io.open(sys.argv[2], encoding='utf-8') if l.strip()]
res = []
for p in paths:
    rel = p.replace('\\', '/')
    r0 = REPO + '/site-packages/'
    if rel.startswith(r0):
        rel = rel[len(r0):]
    prod = os.path.join(build, rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py').replace('\\', '/')
    if not os.path.isfile(prod):
        print('%-40s NO-PRODUCT %s' % (os.path.basename(p), prod))
        continue
    origs = S._load_map(p.replace('/', os.sep))
    try:
        decs = S._compile_map(prod)
    except Exception as e:
        print('%-40s COMPILE-FAIL %s' % (os.path.basename(p), e))
        continue
    names = sorted(set(origs) & set(decs))
    ok, bad = 0, []
    for n in names:
        kind, msg, _ = S.strict_compare(origs[n], decs[n])
        if kind is None:
            ok += 1
        else:
            bad.append([n, kind, msg])
    print('%-40s strict %d/%d missing=%s extra=%s' % (os.path.basename(p), ok, len(names),
                                                      sorted(set(origs) - set(decs)),
                                                      sorted(set(decs) - set(origs))))
    for b in bad:
        print('      %-30s [%s] %s' % (b[0][:30], b[1], b[2][:120]))
    res.append({'pyc': p, 'ok': ok, 'n': len(names), 'bad': bad})
if len(sys.argv) > 3:
    io.open(sys.argv[3], 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
