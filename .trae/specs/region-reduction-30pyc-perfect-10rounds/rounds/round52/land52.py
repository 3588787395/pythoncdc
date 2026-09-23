# -*- coding: utf-8 -*-
"""Round 52 landing: apply the two gated specs to the worktree core and prove the
result is byte-identical to the gated combined arm mirror (mirr_c52ab).

Any mismatch aborts BEFORE a byte is written: the file is only replaced after the
in-memory result has been compared with the arm that passed G0/G1/G2'/G3/G4/G4'.
"""
import hashlib
import io
import json
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r52gate'
CR = chr(13)
sys.stdout.reconfigure(encoding='utf-8')

SPECS = [ROOT + '/spec_r52b.json', ROOT + '/spec_r52a.json']
NEW = {}
for sp in SPECS:
    spec = json.load(io.open(sp, encoding='utf-8'))
    rel = spec['file']
    p = os.path.join(REPO, rel.replace('/', os.sep))
    arm = os.path.join(ROOT, 'mirr_c52ab', rel.replace('/', os.sep))
    raw = io.open(p, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    src = raw.decode('utf-8-sig')
    nl = '\r\n' if src.count(CR) else '\n'
    u = src.replace(nl, '\n')
    edits = spec.get('edits') or [{'anchor': spec['anchor'], 'repl': spec['repl']}]
    out = u
    for k, e in enumerate(edits):
        n = out.count(e['anchor'])
        assert n == 1, '%s edit %d anchor occurrences=%d' % (rel, k, n)
        out = out.replace(e['anchor'], e['repl'])
    body = out.replace('\n', nl).encode('utf-8')
    if bom:
        body = b'\xef\xbb\xbf' + body
    arm_raw = io.open(arm, 'rb').read()
    assert body == arm_raw, '%s: landing bytes differ from gated arm mirror' % rel
    NEW[rel] = (p, body, bom, nl, len(edits))

for rel, (p, body, bom, nl, ned) in NEW.items():
    io.open(p, 'wb').write(body)

print('landed %d file(s)' % len(NEW))
for rel, (p, body, bom, nl, ned) in NEW.items():
    raw = io.open(p, 'rb').read()
    assert raw == body, 'readback mismatch'
    crlf = raw.count(b'\r\n')
    print('%s  sha256[:20]=%s  bytes=%d  CRLF=%d  bareLF=%d  BOM=%s  nl=%s  edits=%d'
          % (rel, hashlib.sha256(raw).hexdigest()[:20], len(raw), crlf,
             raw.count(b'\n') - crlf, bom, 'CRLF' if nl == '\r\n' else 'LF', ned))
    assert raw.count(b'\n') == crlf, 'mixed line endings after landing'
    assert (raw[:3] == b'\xef\xbb\xbf') == bom
