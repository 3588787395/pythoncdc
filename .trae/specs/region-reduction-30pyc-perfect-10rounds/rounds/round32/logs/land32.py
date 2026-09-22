# -*- coding: utf-8 -*-
"""Round 32 landing tool: replay the measured spec onto the real core and refuse to write unless
the replayed bytes are byte-identical to the mirror that produced the gate readings.

usage: python -X utf8 land32.py            # dry run: assertions only
       python -X utf8 land32.py --apply     # write core/cfg/comprehension_generator.py
"""
import hashlib
import io
import json
import os
import sys

REPO = r'F:/Downloads/pythoncdc-main'
MIRR = r'D:/Temp/r32gate/c1/mirr_c'
SEP = chr(92)
sys.stdout.reconfigure(encoding='utf-8')

spec = json.load(io.open(r'D:/Temp/r32gate/c1/spec_r32c.json', encoding='utf-8'))
rel = spec['edits'] and spec['file']
assert rel == 'core/cfg/comprehension_generator.py', rel
real = REPO + SEP + rel.replace('/', SEP)
mirror = MIRR + SEP + rel.replace('/', SEP)

src = io.open(real, encoding='utf-8', newline='').read()
nl = '\r\n' if src.count(chr(13)) else '\n'
u = src.replace(nl, '\n')
patched = u
for k, e in enumerate(spec['edits']):
    n = patched.count(e['anchor'])
    assert n == 1, 'edit %d anchor occurrences=%d' % (k, n)
    patched = patched.replace(e['anchor'], e['repl'])
assert patched != u
out = patched.replace('\n', nl).encode('utf-8')
mb = io.open(mirror, 'rb').read()
assert out == mb, 'replay != measured mirror (%d vs %d bytes)' % (len(out), len(mb))
assert out.count(b'\r\n') == mb.count(b'\r\n') and out.count(b'\n') == out.count(b'\r\n'), 'mixed endings'
print('replay == measured mirror bytes: %d B, %d CRLF lines, sha256 %s'
      % (len(out), out.count(b'\r\n'), hashlib.sha256(mb).hexdigest()[:20]))
if '--apply' in sys.argv:
    tmp = real + '.r32tmp'
    io.open(tmp, 'wb').write(out)
    os.replace(tmp, real)
    after = io.open(real, 'rb').read()
    assert after == mb, 'written bytes differ from mirror'
    print('applied; worktree core now identical to the arm that passed G0-G4: sha256 %s'
          % hashlib.sha256(after).hexdigest()[:20])
else:
    print('dry run (pass --apply to write)')
