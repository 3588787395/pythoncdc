# -*- coding: utf-8 -*-
"""Round 40 G5 canary audit.

Reads the two G4 arm dumps (h_all.jsonl = pre-landing head core, c_all.jsonl = R40-A2 arm),
plus the pinned canary set D:/Temp/r29gate/canary_shas_landed.txt, and reports for every
canary entry:  matched/total on both arms  +  product sha on both arms  +  verdict.

Also reports, corpus-wide, how many of the 402 files changed their product sha while their
official matched count stayed the same (the "text-only" blast radius), because that is the
quantity the byte-identity canary is meant to bound.
"""
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
SCRATCH = r'D:/Temp/r40diagA'
SETS = r'D:/Temp/r29gate/canary_shas_landed.txt'


def load(p):
    d = {}
    for line in io.open(p, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        d[r['path']] = r
    return d


H = load(os.path.join(SCRATCH, 'h_all.jsonl'))
C = load(os.path.join(SCRATCH, 'c_all.jsonl'))
assert len(H) == len(C) == 402, (len(H), len(C))


def find(sub):
    hits = [p for p in H if p.replace('\\', '/').endswith(sub)]
    assert len(hits) == 1, (sub, hits)
    return hits[0]


print('=== pinned canary set (G5 byte-identity guards) ===')
n_moved = 0
n_lost = 0
for line in io.open(SETS, encoding='utf-8'):
    line = line.rstrip('\n')
    if not line.strip():
        continue
    parts = line.split()
    sub = parts[0]
    want = parts[1]
    old_sha = parts[2].split('=', 1)[1]
    p = find(sub)
    a, b = H[p], C[p]
    same_ratio = ('%s/%s' % (a['matched_functions'], a['total_functions'])
                  == '%s/%s' % (b['matched_functions'], b['total_functions']) == want)
    verdict = 'UNCHANGED' if a['sha'] == b['sha'] else 'TEXT-MOVED'
    if a['sha'] != b['sha']:
        n_moved += 1
    if not same_ratio:
        n_lost += 1
    print('%-46s want=%-9s head=%3s/%-3s cand=%3s/%-3s ratio-hold=%s sha %s -> %s  %s'
          % (sub, want, a['matched_functions'], a['total_functions'],
             b['matched_functions'], b['total_functions'], same_ratio,
             a['sha'], b['sha'], verdict))
print('canaries: %d of 9 moved their product text; %d lost official functions' % (n_moved, n_lost))

print('')
print('=== corpus-wide text-only blast radius (official count held, product text moved) ===')
n_sha = n_sha_hold = n_ratio_change = 0
down = []
for p in sorted(H):
    a, b = H[p], C[p]
    if a.get('error') or b.get('error'):
        print('ERR-ROW', p, a.get('error'), b.get('error'))
        continue
    if a['sha'] != b['sha']:
        n_sha += 1
        if a['matched_functions'] == b['matched_functions']:
            n_sha_hold += 1
        else:
            n_ratio_change += 1
            if b['matched_functions'] < a['matched_functions']:
                down.append((p, a['matched_functions'], b['matched_functions']))
print('files whose product text moved           : %d' % n_sha)
print('  ... official matched count unchanged   : %d' % n_sha_hold)
print('  ... official matched count changed     : %d' % n_ratio_change)
print('  ... of which DECREASED (hard NO-GO)    : %d' % len(down))
for d in down:
    print('   DOWN', d)
