# -*- coding: utf-8 -*-
"""A/B the mandated ruler (scripts/pyc_verify.py single) between two fresh arms.

usage: python -X utf8 mand_ab.py <list.txt> <armA> <armB> <out.json>
Both arms must have products under center/build_<arm>/.
"""
import io
import json
import os
import re
import subprocess
import sys

REPO = r'F:/Downloads/pythoncdc-main'
ROOT = r'D:/Temp/opencode/r75gate/center'
PY = sys.executable
sys.stdout.reconfigure(encoding='utf-8')


def prod(pyc, arm):
    rel = pyc.replace('\\', '/')
    pre = REPO.replace('\\', '/') + '/site-packages/'
    if rel.startswith(pre):
        rel = rel[len(pre):]
    return os.path.join(ROOT, 'build_' + arm,
                        rel.replace('/', '__')[:-4] + 'OK.py').replace('\\', '/')


def run(pyc, source=None):
    cmd = [PY, '-X', 'utf8', os.path.join(REPO, 'scripts', 'pyc_verify.py'),
           'single', pyc] + (['--source', source] if source else [])
    p = subprocess.run(cmd, capture_output=True)
    out = (p.stdout or b'').decode('utf-8', 'replace') + (p.stderr or b'').decode('utf-8', 'replace')
    m = re.search(r'status=(\w+) units=(\d+)/(\d+) success_rate=([\d.]+)%', out)
    fails = re.findall(r'\*\*\*([^:]+):\s*(.+)', out)
    if not m:
        return {'raw': out[-600:]}
    return {'status': m.group(1), 'units': [int(m.group(2)), int(m.group(3))],
            'rate': float(m.group(4)), 'fails': fails}


def main():
    lst, a, b, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    res = {}
    nclear = nnew = 0
    for line in io.open(lst, encoding='utf-8'):
        pyc = line.strip()
        if not pyc:
            continue
        pa, pb = prod(pyc, a), prod(pyc, b)
        ra = run(pyc, pa)
        rb = run(pyc, pb)
        key = pyc.replace('\\', '/').split('/site-packages/')[-1]
        res[key] = {a: ra, b: rb}
        fa = set(x[0] for x in ra.get('fails') or [])
        fb = set(x[0] for x in rb.get('fails') or [])
        cl = sorted(fa - fb)
        nw = sorted(fb - fa)
        nclear += len(cl)
        nnew += len(nw)
        print('%-46s %s=%s %s | %s=%s %s' % (
            key, a, ra.get('status'), ra.get('units'),
            b, rb.get('status'), rb.get('units')))
        for x in cl:
            print('    CLEARED  %s' % x)
        for x in nw:
            print('    NEW      %s' % x)
    io.open(out, 'w', encoding='utf-8').write(json.dumps(res, ensure_ascii=False, indent=1))
    print('TOTAL CLEARED=%d NEW=%d  wrote %s' % (nclear, nnew, out))


main()
