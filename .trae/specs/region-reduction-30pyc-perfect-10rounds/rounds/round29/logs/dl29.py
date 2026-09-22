# -*- coding: utf-8 -*-
"""Print the STRICT ruler's own first-divergence window for a function, for every arm asked for.

Unlike the token-text dumper (which reports a false divergence on code-object reprs whose
memory addresses differ), this parses the index out of the strict comparison verdict, so the
window it prints is the one the gate actually fails on.

  python -X utf8 dl29.py --pyc=<file.pyc> --fn=<name> [--arms=landed] [--n=12]
"""
import importlib.util
import io
import os
import re
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r29gate'
BS = chr(92)
sys.stdout.reconfigure(encoding='utf-8')

a = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
pyc = a['pyc'].replace(BS, '/')
want = a['fn']
arms = (a.get('arms', 'landed')).split(',')
n_ctx = int(a.get('n', 12))

_s = importlib.util.spec_from_file_location('r10', os.path.join(REPO, '_r10_strict_check.py'))
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

orig = r10._load_map(pyc)
key = want if want in orig else ([k for k in orig if k.endswith('.' + want)] or [k for k in orig if k == want])[0]
O = r10.filtered(orig[key])
print('=== %s :: %s  orig=%d' % (pyc.split('site-packages/')[-1], key, len(O)))


def tok(i):
    av = i.argval
    if isinstance(av, str) and len(av) > 24:
        av = av[:24] + '~'
    try:
        off = i.offset
    except Exception:
        off = getattr(i, 'start_offset', -1)
    return '%-30s %-26s @%-5s' % (i.opname, av, off)


for arm in arms:
    rel = pyc.replace(REPO.replace(BS, '/') + '/site-packages/', '')[:-4].replace('/', '__') + 'OK.py'
    prod = os.path.join(ROOT, 'build_' + arm, rel.replace(':', '_'))
    if not os.path.isfile(prod):
        print('%-8s no product at %s' % (arm, prod))
        continue
    dec = r10._compile_map(prod)
    if key not in dec:
        hits = [k for k in dec if k.endswith(want)]
        print('%-8s key absent; candidates %s' % (arm, hits))
        if not hits:
            continue
        key2 = hits[0]
    else:
        key2 = key
    D = r10.filtered(dec[key2])
    kind, msg, is_def = r10.strict_compare(orig[key], dec[key2])
    print('%-8s decomp=%d clean=%s  verdict=%s %s' % (arm, len(D), is_def, kind, msg))
    m = re.search(r'#(\d+)', msg or '')
    n = int(m.group(1)) if m else 0
    for k in range(max(0, n - 3), min(len(O), n + n_ctx)):
        print('    o#%-4d %s' % (k, tok(O[k])))
    print('     ---')
    for k in range(max(0, n - 3), min(len(D), n + n_ctx)):
        print('    d#%-4d %s' % (k, tok(D[k])))
