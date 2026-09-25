# -*- coding: utf-8 -*-
"""Center-side independent check of diag0's debug-import cleanup spec.

Read-only over the repo: no writes, no decompiler run.
  python -X utf8 vfy65b0.py
"""
import ast
import io
import json
import os
import py_compile
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8')
CR = chr(13)
REPO = r'F:/Downloads/pythoncdc-main'
SPEC = r'D:/Temp/opencode/r65gate/diag0/specs/cand_r65b0_stripdbg.json'

rel = json.load(io.open(SPEC, encoding='utf-8'))['file']
raw = io.open(os.path.join(REPO, rel.replace('/', os.sep)), 'rb').read()
bom = raw[:3] == b'\xef\xbb\xbf'
text = raw.decode('utf-8-sig')
nl = '\r\n' if text.count(CR) else '\n'
u = text.replace('\r\n', '\n')
spec = json.load(io.open(SPEC, encoding='utf-8'))
edits = spec['edits']
print('landed  bytes=%d bom=%s CRLF=%d bareLF=%d `_os_dbg` lines=%d'
      % (len(raw), bom, raw.count(b'\r\n'), raw.count(b'\n') - raw.count(b'\r\n'),
         sum(1 for l in u.split('\n') if '_os_dbg' in l)))

cur = u
for i, e in enumerate(edits):
    n = cur.count(e['anchor'])
    assert n == 1, 'edit %d anchor occurrences=%d (chained)' % (i + 1, n)
    cur = cur.replace(e['anchor'], e['repl'])
print('all %d anchors unique under chained replay: OK' % len(edits))

left = [l for l in cur.split('\n') if '_os_dbg' in l]
print('remaining `_os_dbg` lines after cleanup: %d' % len(left))
for l in left[:10]:
    print('   LEFT ' + l.strip()[:100])

out = cur.replace('\n', nl).encode('utf-8')
if bom:
    out = b'\xef\xbb\xbf' + out
d = sum(cur.count('\n') - u.count('\n') for _ in [0])
print('cleaned bytes=%d  delta=%+d  CRLF=%d bareLF=%d bom=%s'
      % (len(out), len(out) - len(raw), out.count(b'\r\n'),
         out.count(b'\n') - out.count(b'\r\n'), out[:3] == b'\xef\xbb\xbf'))
import hashlib
print('cleaned sha256[0:12] =', hashlib.sha256(out).hexdigest()[:12])
tmp = os.path.join(tempfile.gettempdir(), 'r65_vfy0_clean.py')
io.open(tmp, 'wb').write(out)
py_compile.compile(tmp, doraise=True, cfile=tmp + 'c')
tree = ast.parse(out.decode('utf-8-sig'))
print('py_compile + ast.parse on cleaned bytes: OK  (statements=%d)' % len(tree.body))
