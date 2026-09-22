# -*- coding: utf-8 -*-
"""Round 41 G5 canary audit (measured, not carried forward).

Compares the two G4 arm dumps -- landed41.jsonl (pre-landing core) and g4_r41b2.jsonl
(R41-B2 candidate core) -- for every entry of the canary set re-derived in Round 40
(D:/Temp/r40gate/canary_shas_landed40.txt).  For each: official matched/total on both arms
plus the product sha on both arms.  Shipping criterion (Round 40 correction): a canary must
not LOSE an official function; product-text movement is reported as observation only.
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
A_FILE = r'D:/Temp/r41gate/landed41.jsonl'
B_FILE = r'D:/Temp/r41gate/g4_r41b2.jsonl'
SET = r'D:/Temp/r40gate/canary_shas_landed40.txt'


def load(p):
    d = {}
    for line in io.open(p, encoding='utf-8'):
        line = line.strip()
        if line:
            r = json.loads(line)
            d[r['path']] = r
    return d


A = load(A_FILE)
B = load(B_FILE)
assert len(A) == len(B) == 402, (len(A), len(B))


def find(sub):
    hits = [p for p in A if p.replace('\\', '/').endswith(sub)]
    assert len(hits) == 1, (sub, hits)
    return hits[0]


n_moved = n_lost = n_base_sha = n_total = 0
for line in io.open(SET, encoding='utf-8'):
    parts = line.split()
    if len(parts) < 3:
        continue
    sub, want, old_sha = parts[0], parts[1], parts[2].split('=', 1)[1]
    p = find(sub)
    a, b = A[p], B[p]
    n_total += 1
    hold = ('%s/%s' % (a['matched_functions'], a['total_functions']) == want)
    if a['sha'] != old_sha:
        n_base_sha += 1
        print('BASELINE-STALE %-40s file says sha=%s but landed arm measured %s'
              % (sub, old_sha, a['sha']))
    if a['sha'] != b['sha']:
        n_moved += 1
    if b['matched_functions'] < a['matched_functions'] or not hold:
        n_lost += 1
    print('%-42s want=%-9s head=%3s/%-3s cand=%3s/%-3s ratio-hold=%-5s sha %s -> %s  %s'
          % (sub, want, a['matched_functions'], a['total_functions'],
             b['matched_functions'], b['total_functions'], hold, a['sha'], b['sha'],
             'UNCHANGED' if a['sha'] == b['sha'] else 'TEXT-MOVED'))
print('')
print('canaries=%d  baseline-sha mismatches vs the landed arm=%d  text-moved=%d  lost-official-function=%d'
      % (n_total, n_base_sha, n_moved, n_lost))
