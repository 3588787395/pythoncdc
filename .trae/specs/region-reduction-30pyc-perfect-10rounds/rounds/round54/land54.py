# -*- coding: utf-8 -*-
"""Land the Round 54 comprehension-ternary hunk.

Applies spec_c54comp.json to the repo file IN MEMORY, then refuses to write unless
the resulting bytes are exactly the bytes of the arm that passed G0/G4/G4'.
"""
import hashlib
import io
import json
import os

REPO = r'F:\Downloads\pythoncdc-main'
CR = b'\r\n'
spec = json.load(io.open(r'D:/Temp/r54mine55/spec_c54comp.json', encoding='utf-8'))
rel = spec['file']
tgt = os.path.join(REPO, rel.replace('/', os.sep))
arm = os.path.join(r'D:/Temp/r54gate/mirr_c54comp', rel.replace('/', os.sep))

raw = io.open(tgt, 'rb').read()
assert raw.count(b'\n') == raw.count(CR), 'target is not pure CRLF'
assert not raw.startswith(b'\xef\xbb\xbf'), 'unexpected BOM'
src = raw.decode('utf-8').replace('\r', '')
for e in spec['edits']:
    assert src.count(e['anchor']) == 1, 'anchor not unique: %d' % src.count(e['anchor'])
    src = src.replace(e['anchor'], e['repl'], 1)
new = src.replace('\n', '\r\n').encode('utf-8')

arm_bytes = io.open(arm, 'rb').read()
if new != arm_bytes:
    print('MISMATCH vs gated arm, aborting. landed-sha=%s arm-sha=%s'
          % (hashlib.sha256(new).hexdigest()[:20], hashlib.sha256(arm_bytes).hexdigest()[:20]))
    raise SystemExit(1)
io.open(tgt, 'wb').write(new)
after = io.open(tgt, 'rb').read()
print('landed %s' % rel)
print('bytes %d -> %d ; CRLF %d ; bare LF %d ; identical-to-arm=%s'
      % (len(raw), len(after), after.count(CR), after.count(b'\n') - after.count(CR),
         after == arm_bytes))
print('sha256[:20] %s -> %s' % (hashlib.sha256(raw).hexdigest()[:20], hashlib.sha256(after).hexdigest()[:20]))
