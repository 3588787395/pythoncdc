# -*- coding: utf-8 -*-
"""Confirmation probe for Round 29 line C/B: does the shared_block post-processing
append load_daily's join block, and with which values?

Two print-only stamps in core/cfg/region_analyzer.py, both inside the
`IF_ELIF_CHAIN._shared_block_info` post-loop (lines 1816-1852):
  P1 -- one line BEFORE `for _cr in self.regions:` (reached once per IF_ELIF_CHAIN
        region that carries a shared_block): prints (_sb, _its, _nm).
  P2 -- one line AFTER the append block (inside `if _nm is not None:`): prints what
        was actually appended into which region, incl. both arms' offsets.

Byte-level insertion, per-line terminators and the BOM are preserved; the script
self-proves that deleting every stamped line reconstructs the original bytes.

  python -X utf8 mkp29c.py
"""
import io
import os
import shutil
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r29gate'
DST = os.path.join(ROOT, 'mirr_p29c')
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


# --- locate the two anchor lines by exact text, and assert each is unique ---------
A1 = 'for _cr in self.regions:'
A2 = '_cr._shared_merge_block = _sb'
t1 = [i for i, l in enumerate(lines) if text(l).strip() == A1]
t2 = [i for i, l in enumerate(lines) if text(l).strip() == A2]
assert len(t1) == 1 and len(t2) == 1, (len(t1), len(t2))
i1, i2 = t1[0], t2[0]
print('anchors: P1 before line %d, P2 after line %d' % (i1 + 1, i2 + 1))

OFFS = "lambda bs: [getattr(b, 'start_offset', '?') for b in (bs or [])]"
P1 = ("__import__('sys').stderr.write('[R29P1] sb=%s its=%s nm=%s\\n' % ("
      "getattr(_sb, 'start_offset', '?'), getattr(_its, 'start_offset', '?'), "
      "getattr(_nm, 'start_offset', '?')))")
P2 = ("__import__('sys').stderr.write('[R29P2] appended sb=%s cr_entry=%s nm=%s "
      "then=%s else=%s\\n' % (getattr(_sb, 'start_offset', '?'), "
      "_cr.entry.start_offset, getattr(_nm, 'start_offset', '?'), "
      "(" + OFFS + ")(_cr.then_blocks), (" + OFFS + ")(_cr.else_blocks)))")

class _B(object):
    def __init__(self, o):
        self.start_offset = o


class _CR(object):
    entry = _B(7)
    then_blocks = [_B(1), _B(2)]
    else_blocks = None


_t = {'_sb': _B(3), '_its': _B(4), '_nm': _B(5), '_cr': _CR()}
exec(compile(P1, '<p1>', 'exec'), _t)
exec(compile(P2, '<p2>', 'exec'), _t)
print('self-test ok: both stamps format and write without raising')

# P2 goes after its anchor (same indent, stays inside `if _nm is not None:`);
# P1 goes BEFORE its anchor (same indent, stays inside `if _sb is not None ...:`).
for idx, src, stamp, after_mode in ((i2, lines[i2], P2, True), (i1, lines[i1], P1, False)):
    txt = text(src)
    ind = txt[:len(txt) - len(txt.lstrip())]
    term = b'\r\n' if src.endswith(b'\r\n') else b'\n'
    lines.insert(idx + 1 if after_mode else idx, (ind + stamp).encode('utf-8') + term)

n2 = sum(1 for l in lines if b'[R29P2]' in l)
assert n2 == 1, n2
out = (b'\xef\xbb\xbf' if bom else b'') + b''.join(lines)
io.open(path, 'wb').write(out)
after = io.open(path, 'rb').read()
assert (after[:3] == b'\xef\xbb\xbf') == bom, 'BOM changed'
src_txt = after.decode('utf-8-sig')
compile(src_txt, 'region_analyzer.py', 'exec')
recon = b''.join(l for l in after.splitlines(keepends=True) if '[R29P' not in l)
assert recon == body, 'delete-stamps did not reconstruct the original bytes'
assert len(src_txt.split('\n')) - len(raw.decode('utf-8-sig').split('\n')) == 2
print('probe mirror built: 2 inserts, %d -> %d bytes, syntax ok, delete-stamps==original'
      % (len(raw), len(after)))
