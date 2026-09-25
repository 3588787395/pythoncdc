# -*- coding: utf-8 -*-
"""diag4 r67: tally a jsonl dump -> battery totals + canary shas."""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
GATE = 'D:/Temp/opencode/r67gate/diag4'
arm = sys.argv[1] if len(sys.argv) > 1 else 'landed'
kind = sys.argv[2] if len(sys.argv) > 2 else 'all'


def rows(name):
    p = os.path.join(GATE, 'dump', '%s_%s.jsonl' % (arm, name))
    return [json.loads(l) for l in io.open(p, encoding='utf-8') if l.strip()]


if kind in ('all', 'battery'):
    R = rows('battery')
    tot = sum(r['total_functions'] for r in R)
    m = sum(r['matched_functions'] for r in R)
    bad = sum(1 for r in R if r['mism'])
    print('BATTERY %s: matched %d/%d  defect-functions %d files=%d' % (arm, m, tot, bad, len(R)))
if kind in ('all', 'targets'):
    for r in rows('targets'):
        print('TARGET  %-28s %s/%s mism=%s' % (os.path.basename(r['path']),
                                               r['matched_functions'], r['total_functions'], r['mism']))
if kind in ('all', 'canary'):
    for r in rows('canary'):
        print('CANARY  %-24s %-4s sha=%s' % (os.path.basename(r['path']),
                                             '%d/%d' % (r['matched_functions'], r['total_functions']), r['sha']))
