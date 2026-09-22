# -*- coding: utf-8 -*-
"""Print, for both round-37 arms, the single unmatched function of every deficit-1 file."""
import io
import json

def rows(f):
    out = []
    for line in io.open(f, encoding='utf-8'):
        if line.strip():
            out.append(json.loads(line))
    return out


for tag, f in (('LANDED  (pre-landing core bbfe1a414032436921ab)', 'r37_landed_d17.jsonl'),
               ('R37A    (candidate)', 'r37a_d17.jsonl')):
    print('========== %s' % tag)
    for r in rows(f):
        if r['matched_functions'] + 1 != r['total_functions']:
            continue
        p = r['path'].replace('\\', '/').split('site-packages/')[-1]
        ms = r.get('mism') or []
        print('%-70s %2d/%2d  %s' % (
            p, r['matched_functions'], r['total_functions'],
            ' | '.join('%s %d/%d j%d t%d' % (m[0].split('.')[-1], m[1], m[2], m[3], m[4])
                       for m in ms)))
