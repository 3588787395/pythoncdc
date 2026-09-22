# -*- coding: utf-8 -*-
"""Build a stamp mirror (D:/Temp/r29gate/mirr_stamp) that prints, for EVERY exact
`merge = else_succ` assignment in core/cfg/region_analyzer.py, which site fired and with
which block offsets -- measured, not read off the source.

  python -X utf8 mkstamp29c.py

Byte-level insertion: each existing line keeps its own terminator (the file's mixed CRLF/LF
is never normalised), the stamp copies the terminator of the line it follows, and the script
self-proves that deleting every stamped line reconstructs the original bytes exactly.
Line-number based, so sites whose text is identical still get distinct stamps. The stamp
reads through locals() so it cannot raise a NameError and alter the run it observes.
"""
import io
import os
import shutil
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r29gate'
DST = os.path.join(ROOT, 'mirr_stamp')
REL = os.path.join('core', 'cfg', 'region_analyzer.py')
BS = os.sep
sys.stdout.reconfigure(encoding='utf-8')

if os.path.isdir(DST):
    shutil.rmtree(DST)
shutil.copytree(os.path.join(REPO, 'core'), os.path.join(DST, 'core'))
shutil.copy(os.path.join(REPO, 'pycdc.py'), os.path.join(DST, 'pycdc.py'))

path = os.path.join(DST, REL)
raw = io.open(path, 'rb').read()
bom = raw[:3] == b'\xef\xbb\xbf'
body = raw[3:] if bom else raw
lines = body.splitlines(keepends=True)


def text(ln):
    return ln.decode('utf-8').rstrip('\r\n')


targets = [i for i, l in enumerate(lines) if text(l).strip() == 'merge = else_succ']
print('exact `merge = else_succ` sites:', [i + 1 for i in targets])
for i in sorted(targets, reverse=True):
    src = text(lines[i])
    ind = src[:len(src) - len(src.lstrip())]
    term = b'\r\n' if lines[i].endswith(b'\r\n') else b'\n'
    n = str(i + 1)
    stamp = (ind + "__import__('sys').stderr.write('[R29S] else=%s then=%s entry=%s" +
             " line=" + n + "\\n' % (" +
             "getattr(locals().get('else_succ'), 'start_offset', '?')"
             ", getattr(locals().get('then_succ'), 'start_offset', '?')"
             ", getattr(locals().get('entry'), 'start_offset', '?')))")
    assert stamp.count('%s') == 3 and stamp.count('getattr(') == 3, stamp
    lines.insert(i + 1, stamp.encode('utf-8') + term)

out = (b'\xef\xbb\xbf' if bom else b'') + b''.join(lines)
io.open(path, 'wb').write(out)
after = io.open(path, 'rb').read()
assert (after[:3] == b'\xef\xbb\xbf') == bom, 'BOM changed'
compile(after.decode('utf-8-sig'), 'region_analyzer.py', 'exec')
rebuilt = b''.join(l for l in after[3 if bom else 0:].splitlines(keepends=True)
                   if b'[R29S]' not in l)
assert rebuilt == body, 'stamping was not purely additive'
print('stamp mirror built: %d inserts, %d -> %d bytes, syntax ok, delete-stamps==original'
      % (len(targets), len(raw), len(after)))
