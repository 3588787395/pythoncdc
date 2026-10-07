import dis
import glob
import json
import marshal
import os
import re
import sys
import types
from collections import Counter

BS = chr(92)
ROOT = os.getcwd()
BASE = os.path.join(ROOT, '.trae', 'specs', 'region-reduction-v3-full-corpus-100pct-10rounds')
NOISE = ('NOP', 'CACHE', 'EXTENDED_ARG')


def walk(co, path):
    yield path, co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            yield from walk(c, path + '/' + c.co_name)


def seq(co):
    out = []
    for i in dis.get_instructions(co):
        arg = i.argrepr
        if i.opname.startswith(('JUMP', 'FOR_ITER', 'POP_JUMP')) and 'to ' in arg:
            arg = 'to#' + arg.split('to ')[-1]
        if isinstance(i.argval, types.CodeType):
            arg = '<co:%s>' % i.argval.co_name
        out.append((i.opname, arg, i.offset))
    return out


def strip_nop(s):
    real = [x for x in s if x[0] not in NOISE]
    # relabel jump targets by index into the stripped sequence
    off2idx = {x[2]: n for n, x in enumerate(s)}
    idx2new = {}
    for n, x in enumerate(s):
        if x[0] not in NOISE:
            idx2new[off2idx[x[2]]] = len(idx2new)
    res = []
    for x in real:
        op, arg = x[0], x[1]
        if arg.startswith('to#'):
            t = idx2new.get(off2idx.get(int(arg[3:]), -1), int(arg[3:]))
            arg = 'to>%d' % t
        res.append((op, arg))
    return res


rows = []
for p in sorted(glob.glob(os.path.join(BASE, 'rounds', 'round8', 'after', 'shard*_report.json'))):
    d = json.load(open(p, encoding='utf-8'))
    for r in d['rows']:
        if r['status'] == 'success':
            continue
        pyc = r['pyc'].replace(BS, '/')
        for f in r['failures']:
            rows.append((pyc, f.split(': ')[0].replace('***', '')))

cnt = Counter()
detail = []
cache = {}
for pyc, unit in rows:
    m = unit.split('.')[-1]
    if pyc not in cache:
        try:
            o = dict(walk(marshal.loads(open(pyc, 'rb').read()[16:]), ''))
            prod = pyc[:-4] + 'OK.py'
            dmap = dict(walk(compile(open(prod, encoding='utf-8').read(), prod, 'exec'), ''))
        except Exception as e:
            o, dmap = {}, {}
            detail.append(('ERROR', unit, str(e)[:50]))
        cache[pyc] = (o, dmap)
    o, dmap = cache[pyc]
    oc = [v for k, v in o.items() if k.endswith('/' + m)]
    dc = [v for k, v in dmap.items() if k.endswith('/' + m)]
    if not oc or not dc:
        cnt['NOTFOUND'] += 1
        continue
    so, sd = seq(oc[0]), seq(dc[0])
    no = sum(1 for x in so if x[0] in NOISE)
    nd = sum(1 for x in sd if x[0] in NOISE)
    to, td = strip_nop(so), strip_nop(sd)
    if to == td:
        k = 'NOP_ONLY'
    elif len(to) == len(td):
        diff = sum(1 for a, b in zip(to, td) if a != b)
        k = 'NOP_ONLY' if False else 'STRUCT_EQUAL_LEN(%d)' % diff
    else:
        k = 'STRUCT_DIFFER'
    cnt[k] += 1
    detail.append((k, unit, 'nop_orig=%d nop_dec=%d len %d/%d' % (no, nd, len(to), len(td))))

for k, v, d in detail:
    print('%-22s %-50s %s' % (k, v[-50:], d))
print('TOTAL=%d' % len(rows))
for k, v in cnt.most_common():
    print('%-22s %d' % (k, v))
