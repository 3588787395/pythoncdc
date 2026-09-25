# -*- coding: utf-8 -*-
"""diag4 helper: per-function mismatch table for one/two arm dumps."""
import io
import json
import sys


def load(p):
    r = {}
    for l in io.open(p, encoding='utf-8'):
        l = l.strip()
        if not l:
            continue
        d = json.loads(l)
        key = d['path'].replace('\\', '/').split('site-packages/')[-1]
        r[key] = d
    return r


def main():
    arms = sys.argv[1:] or ['dump/landed.jsonl']
    data = [(a.split('/')[-1].replace('.jsonl', ''), load(a)) for a in arms]
    files = []
    for _, d in data:
        for k in d:
            if k not in files:
                files.append(k)
    for f in files:
        head = ' == '.join('%s %s/%s' % (n, d[f]['matched_functions'], d[f]['total_functions'])
                           for n, d in data if f in d)
        print('### %s\n    %s' % (f, head))
        rows = {}
        for n, d in data:
            if f not in d:
                continue
            for m in d[f]['mism']:
                rows.setdefault(m[0], {})[n] = m
        for fn in sorted(rows):
            cells = []
            for n, d in data:
                m = rows[fn].get(n)
                cells.append('%s=%s' % (n, ('%d/%d jd%d t%d' % (m[1], m[2], m[3], m[4])) if m else 'MATCH'))
            print('    %-40s %s' % (fn, '  '.join(cells)))


main()
