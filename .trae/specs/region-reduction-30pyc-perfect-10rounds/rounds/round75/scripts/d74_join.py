# -*- coding: utf-8 -*-
"""d74_join.py -- join fam74 (77 units) with the centre probes firstdiv73 /
exctable_diff73 / tryverdict73 / crosstab74, and report which unit(s) are NOT
covered by the centre probes.  Read-only.  Writes dump/units75_join.json + .tsv
and dump/join_gap.txt.
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.abspath(__file__))
DUMP = os.path.join(ROOT, 'dump')
CENTER = r'D:/Temp/opencode/r75gate/center/dump'


def norm(nm):
    return nm.strip()


def main():
    fam = json.load(io.open(os.path.join(ROOT, 'fam75.json'), encoding='utf-8'))
    # firstdiv75.txt
    fd = {}
    for ln in io.open(os.path.join(CENTER, 'firstdiv75.txt'), encoding='utf-8'):
        if '|' not in ln:
            continue
        p = [x.strip() for x in ln.split('|')]
        key = (p[0], p[1])
        m = re.search(r'origTryDepth=(\d+) prodTryDepth=(\d+)', ln)
        fd[key] = {'kind': p[2], 'div': p[3],
                   'firstdiv': 'Y' if 'firstdiv=Y' in ln else 'N',
                   'off': int(re.search(r'off=(-?\d+)', ln).group(1)),
                   'origTryDepth': int(m.group(1)), 'prodTryDepth': int(m.group(2))}
    # exctable_diff75.txt
    ex = {}
    for ln in io.open(os.path.join(CENTER, 'exctable_diff75.txt'), encoding='utf-8'):
        if '|' not in ln or 'et=' in ln or 'origNest' not in ln:
            continue
        p = [x.strip() for x in ln.split('|')]
        m = re.search(r'origNest=(\d+) prodNest=(\d+) origEnts=(\d+) prodEnts=(\d+)', ln)
        ex[(p[0], p[1])] = {'same': p[2], 'origNest': int(m.group(1)),
                            'prodNest': int(m.group(2)),
                            'origEnts': int(m.group(3)), 'prodEnts': int(m.group(4))}
    # tryverdict75.txt
    tv = {}
    for ln in io.open(os.path.join(CENTER, 'tryverdict75.txt'), encoding='utf-8'):
        if '|' not in ln:
            continue
        p = [x.strip() for x in ln.split('|')]
        m = re.search(r'et=(\d+) nest=(\d+) prodTryNest=(\d+)', ln)
        if not m:
            continue
        tv[(p[0], p[1])] = {'et': int(m.group(1)), 'nest': int(m.group(2)),
                            'prodTryNest': int(m.group(3))}
    # crosstab75.txt  file / name / family / verdict / IN-OUT / verdict
    ct = {}
    for ln in io.open(os.path.join(DUMP, 'crosstab75.txt'), encoding='utf-8'):
        p = [x.strip() for x in ln.split('\t')]
        if len(p) < 6:
            continue
        ct[(p[0].split('/')[-1], p[1])] = {'fam': p[2], 'verdict': p[3],
                                           'intry': int(p[4])}

    rows = []
    gap = []
    seen = {}
    for r in fam:
        key = (r['file'].split('/')[-1], r['name'])
        seen[key] = seen.get(key, 0) + 1
        row = dict(r)
        row['pyc_base'] = r['file'].split('/')[-1]
        row.update({'fd': fd.get(key), 'ex': ex.get(key), 'tv': tv.get(key),
                    'ct': ct.get(key)})
        if row['fd'] is None or row['ex'] is None or row['tv'] is None:
            gap.append({'key': key, 'fd': row['fd'] is not None,
                        'ex': row['ex'] is not None, 'tv': row['tv'] is not None})
        rows.append(row)

    json.dump(rows, io.open(os.path.join(DUMP, 'units75_join.json'), 'w',
                            encoding='utf-8', newline='\n'),
              ensure_ascii=False, indent=1)

    # tsv
    cols = ['pyc_base', 'name', 'family', 'verdict', 'cat', 'reason', 'lenA', 'lenB',
            'firstidx', 'firstA', 'firstB', 'lineA', 'lineB']
    out = ['\t'.join(cols + ['intry', 'fd_off', 'fd_origTryDepth', 'ex_same',
                             'ex_origEnts', 'ex_prodEnts', 'tv_et', 'tv_nest',
                             'tv_prodTryNest'])]
    for r in rows:
        fdx, exx, tvx, ctx = r['fd'], r['ex'], r['tv'], r['ct']
        vals = [str(r.get(c, '')) for c in cols]
        vals += [str(ctx['intry']) if ctx else '',
                 str(fdx['off']) if fdx else '',
                 str(fdx['origTryDepth']) if fdx else '',
                 exx['same'] if exx else '',
                 str(exx['origEnts']) if exx else '',
                 str(exx['prodEnts']) if exx else '',
                 str(tvx['et']) if tvx else '',
                 str(tvx['nest']) if tvx else '',
                 str(tvx['prodTryNest']) if tvx else '']
        out.append('\t'.join(vals))
    io.open(os.path.join(DUMP, 'units75_join.tsv'), 'w', encoding='utf-8',
            newline='\n').write('\n'.join(out) + '\n')

    # gap report: fam74 keys not present in centre probes, and centre keys not in fam74
    famkeys = set((r['pyc_base'], r['name']) for r in rows)
    allfd = set(fd.keys())
    msg = []
    msg.append('fam74 units = %d' % len(rows))
    msg.append('firstdiv73 rows = %d ; exctable rows = %d ; tryverdict rows = %d'
               % (len(fd), len(ex), len(tv)))
    msg.append('fam74 NOT in firstdiv73: %s' % sorted(famkeys - allfd))
    msg.append('firstdiv73 NOT in fam74: %s' % sorted(allfd - famkeys))
    msg.append('duplicate (pyc,name) in fam74: %s'
               % sorted(k for k, v in seen.items() if v > 1))
    msg.append('join gaps (missing centre rows): %s' % json.dumps(gap, ensure_ascii=False))
    io.open(os.path.join(DUMP, 'join_gap.txt'), 'w', encoding='utf-8',
            newline='\n').write('\n'.join(msg) + '\n')
    print('\n'.join(msg))

    # family x IN counts (verify crosstab totals)
    from collections import Counter
    c = Counter((r['family'], r['ct']['intry'] if r['ct'] else None) for r in rows)
    print('family x intry:', dict(c))
    print('families:', dict(Counter(r['family'] for r in rows)))


if __name__ == '__main__':
    main()
