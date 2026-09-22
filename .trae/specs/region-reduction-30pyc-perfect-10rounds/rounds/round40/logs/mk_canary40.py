# -*- coding: utf-8 -*-
"""Round 41 G5 baseline: re-derive the pinned byte-identity canary set from the LANDED products.

Same 9 entries as D:/Temp/r29gate/canary_shas_landed.txt (that file was last re-derived in
Round 29 and three of its shas are now stale). For each entry the product on disk is
normalised the way the mirror harness hashes it (decompiled text == LF form of the product:
the repo writes CRLF, git stores LF), so the sha here is directly comparable with the
`sha` field of an r38m arm dump.
"""
import hashlib
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
OLD = r'D:/Temp/r29gate/canary_shas_landed.txt'
NEW = r'D:/Temp/r40gate/canary_shas_landed40.txt'

idx = {}
for rec in json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8')):
    idx[rec['path'].replace('\\', '/')] = rec

rows = []
for line in io.open(OLD, encoding='utf-8'):
    if not line.strip():
        continue
    sub, want, shafield = line.split()[0], line.split()[1], line.split()[2]
    hits = [p for p in idx if p.endswith(sub)]
    assert len(hits) == 1, (sub, hits)
    p = hits[0]
    prod = p[:-4] + 'OK.py'
    raw = io.open(os.path.join(REPO, prod), 'rb').read()
    lf = raw.replace(b'\r\n', b'\n')
    got = hashlib.sha256(lf).hexdigest()[:16]
    rec = idx[p]
    ratio = '%s/%s' % (rec['matched_functions'], rec['function_count'])
    assert ratio == want, (sub, ratio, want)
    rows.append('%-52s %-9s sha=%s' % (sub, ratio, got))

os.makedirs(os.path.dirname(NEW), exist_ok=True)
body = '\n'.join(rows) + '\n'
io.open(NEW, 'w', encoding='utf-8', newline='').write(body)
print(body)
print('wrote %s (%d entries, ratios verified against pyc_index.json)' % (NEW, len(rows)))
