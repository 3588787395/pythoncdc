import dis
import glob
import json
import marshal
import os
import sys
import types
from collections import Counter

BS = chr(92)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, ROOT)

BASE = os.path.join(ROOT, '.trae', 'specs', 'region-reduction-v3-full-corpus-100pct-10rounds')


def walk(co, path):
    yield path, co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            yield from walk(c, path + '/' + c.co_name)


def instrs(co):
    return list(dis.get_instructions(co))


def classify(pyc, prod, unit):
    name = unit.split(':')[-1]
    m = name.split('.')[-1]
    try:
        mod = marshal.loads(open(pyc, 'rb').read()[16:])
        o_map = dict(walk(mod, ''))
        src = compile(open(prod, encoding='utf-8').read(), prod, 'exec')
        d_map = dict(walk(src, ''))
    except Exception as e:
        return ('ERROR', str(e)[:60])
    oc = [v for k, v in o_map.items() if k.endswith('/' + m)]
    dc = [v for k, v in d_map.items() if k.endswith('/' + m)]
    if not oc or not dc:
        return ('NOTFOUND', m)
    oi = instrs(oc[0])
    di = instrs(dc[0])
    for n, (a, b) in enumerate(zip(oi, di)):
        if a.opname != b.opname or a.argrepr != b.argrepr:
            if a.opname == 'NOP' and b.opname != 'NOP':
                return ('NOP_BOUNDARY', 'n=%d line=%s' % (n, a.starts_line))
            if a.opname == b.opname and a.argrepr != b.argrepr and a.opname.startswith(('POP_JUMP', 'JUMP', 'FOR_ITER')):
                try:
                    delta = int(a.argrepr.split()[-1]) - int(b.argrepr.split()[-1])
                except Exception:
                    delta = None
                return ('TARGET_DELTA', '%s d=%s' % (a.opname, delta))
            if a.opname != b.opname and a.argrepr == b.argrepr:
                return ('POLARITY', '%s vs %s' % (a.opname, b.opname))
            return ('OTHER', 'n=%d %s/%s vs %s/%s' % (n, a.opname, a.argrepr, b.opname, b.argrepr))
    if len(oi) != len(di):
        return ('LEN', '%d vs %d' % (len(oi), len(di)))
    return ('EQUAL', '')


rows = []
for p in sorted(glob.glob(os.path.join(BASE, 'rounds', 'round8', 'after', 'shard*_report.json'))):
    d = json.load(open(p, encoding='utf-8'))
    for r in d['rows']:
        if r['status'] == 'success':
            continue
        pyc = r['pyc'].replace(BS, '/')
        prod = pyc[:-4] + 'OK.py'
        for f in r['failures']:
            unit = f.split(': ')[0].replace('***', '')
            rows.append((pyc, prod, unit))

cnt = Counter()
for pyc, prod, unit in rows:
    k, detail = classify(pyc, prod, unit)
    cnt[k] += 1
    print('%-14s %-46s %s' % (k, unit[-46:], detail))
print('TOTAL_UNITS=%d' % len(rows))
for k, v in cnt.most_common():
    print('%-14s %d' % (k, v))
