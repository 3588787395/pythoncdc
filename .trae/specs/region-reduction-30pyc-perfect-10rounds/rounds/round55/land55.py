# -*- coding: utf-8 -*-
"""Land a spec onto the repo core only if the result equals the gated arm bytes.

usage: python -X utf8 land55.py <spec.json> <arm-mirror-dir>
"""
import hashlib
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
CR = b'\r\n'
spec = json.load(io.open(sys.argv[1], encoding='utf-8'))
ARMDIR = os.path.abspath(sys.argv[2])
rel = spec['file']
tgt = os.path.join(REPO, rel.replace('/', os.sep))
arm = os.path.join(ARMDIR, rel.replace('/', os.sep))

raw = io.open(tgt, 'rb').read()
BOM = b'\xef\xbb\xbf'
has_bom = raw.startswith(BOM)
body = raw[len(BOM):] if has_bom else raw
assert body.count(b'\n') == body.count(CR), 'target is not pure CRLF'
src = body.decode('utf-8').replace('\r', '')
for e in spec['edits']:
    assert src.count(e['anchor']) == 1, 'anchor count %d' % src.count(e['anchor'])
    src = src.replace(e['anchor'], e['repl'], 1)
new = (BOM if has_bom else b'') + src.replace('\n', '\r\n').encode('utf-8')
arm_bytes = io.open(arm, 'rb').read()
if new != arm_bytes:
    print('ABORT: built bytes != gated arm bytes')
    raise SystemExit(1)
io.open(tgt, 'wb').write(new)
after = io.open(tgt, 'rb').read()
print('landed %s' % rel)
print('bytes %d -> %d ; CRLF %d ; bare LF %d ; == gated arm: %s'
      % (len(raw), len(after), after.count(CR), after.count(b'\n') - after.count(CR),
         after == arm_bytes))
print('sha256[:20] %s -> %s' % (hashlib.sha256(raw).hexdigest()[:20],
                                hashlib.sha256(after).hexdigest()[:20]))
