# -*- coding: utf-8 -*-
"""Round 29 probe #2: WHO puts join block @2478 into an IfRegion's then_blocks for
`fly/dumpload/load_daily.pyc :: <module>`.

D1 -- one gate stamp immediately BEFORE each of the three `region = IfRegion(`
      constructions in core/cfg/region_analyzer.py (lines 17888 / 19304 / 19458), printing
      the site id, the cfg name, the entry, the merge the region is built with and both
      arm block lists.  Fires only when 2478 is in the arm list being handed over.
D2 -- one gate stamp before region_ast_generator.py:14351, the consumption point B's stack
      proved is reached with 2478 in `region.then_blocks`, printing the FINAL region state.
      Comparing D1 and D2 says whether the claim exists at construction or was added later.

Byte-level insertion; per-line terminators and BOM preserved; self-proves that deleting
every stamped line reconstructs the original bytes, and that both stamped files compile.

  python -X utf8 mkp29d.py
"""
import io
import os
import shutil
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r29gate'
DST = os.path.join(ROOT, 'mirr_p29d')
BS = os.sep
TGT = 2478
sys.stdout.reconfigure(encoding='utf-8')

if os.path.isdir(DST):
    shutil.rmtree(DST)
shutil.copytree(os.path.join(REPO, 'core'), os.path.join(DST, 'core'))
shutil.copy(os.path.join(REPO, 'pycdc.py'), os.path.join(DST, 'pycdc.py'))

OFFS = "lambda bs: [getattr(b, 'start_offset', '?') for b in (bs or [])]"
ANALYZER = os.path.join('core', 'cfg', 'region_analyzer.py')
GENERATOR = os.path.join('core', 'cfg', 'region_ast_generator.py')

# (relpath, mode, anchor, stamp)  mode: 'before' -> same indent, previous line
JOBS = [
    (ANALYZER, 17888, 'region = IfRegion(',
     "if any(getattr(b, 'start_offset', -1) == %d for b in then_blocks): "
     "__import__('sys').stderr.write('[R29D1] site=17888 cfg=%%s entry=%%s merge=%%s "
     "else=%%s then=%%s\\n' %% (self.cfg.name, getattr(block, 'start_offset', '?'), "
     "getattr(merge, 'start_offset', '?'), (%s)(else_blocks), (%s)(then_blocks)))"
     % (TGT, OFFS, OFFS)),
    (ANALYZER, 19304, 'region = IfRegion(',
     "if any(getattr(b, 'start_offset', -1) == %d for b in then_blocks): "
     "__import__('sys').stderr.write('[R29D1] site=19304 cfg=%%s entry=%%s merge=%%s "
     "else=%%s then=%%s\\n' %% (self.cfg.name, getattr(block, 'start_offset', '?'), "
     "getattr(merge, 'start_offset', '?'), (%s)(else_blocks), (%s)(then_blocks)))"
     % (TGT, OFFS, OFFS)),
    (ANALYZER, 19458, 'region = IfRegion(',
     "if any(getattr(b, 'start_offset', -1) == %d for b in _blocks): "
     "__import__('sys').stderr.write('[R29D1] site=19458 cfg=%%s entry=%%s merge=%%s "
     "else=%%s then=%%s\\n' %% (self.cfg.name, getattr(header, 'start_offset', '?'), "
     "getattr(merge_block, 'start_offset', '?'), (%s)(else_blocks), (%s)(_blocks)))"
     % (TGT, OFFS, OFFS)),
    (GENERATOR, 14351, "then_stmts = self._process_if_blocks(region.then_blocks, region, branch='then',",
     "if any(getattr(b, 'start_offset', -1) == %d for b in (region.then_blocks or [])): "
     "__import__('sys').stderr.write('[R29D2] FINAL cfg=%%s entry=%%s merge=%%s "
     "else=%%s then=%%s\\n' %% (self.cfg.name, region.entry.start_offset, "
     "getattr(region.merge_block, 'start_offset', '?'), (%s)(getattr(region, 'else_blocks', None)), "
     "(%s)(region.then_blocks)))" % (TGT, OFFS, OFFS)),
]


def text(ln):
    return ln.decode('utf-8').rstrip('\r\n')


for rel in (ANALYZER, GENERATOR):
    path = os.path.join(DST, rel)
    raw = io.open(path, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    body = raw[3:] if bom else raw
    lines = body.splitlines(keepends=True)
    jobs = [j for j in JOBS if j[0] == rel]
    for _, lineno, anchor, stamp in sorted(jobs, key=lambda j: -j[1]):
        i = lineno - 1
        assert text(lines[i]).strip() == anchor, (lineno, text(lines[i])[:80])
        src = text(lines[i])
        ind = src[:len(src) - len(src.lstrip())]
        term = b'\r\n' if lines[i].endswith(b'\r\n') else b'\n'
        lines.insert(i, (ind + stamp).encode('utf-8') + term)
    out = (b'\xef\xbb\xbf' if bom else b'') + b''.join(lines)
    io.open(path, 'wb').write(out)
    after = io.open(path, 'rb').read()
    assert (after[:3] == b'\xef\xbb\xbf') == bom, 'BOM changed'
    compile(after.decode('utf-8-sig'), rel, 'exec')
    recon = b''.join(l for l in after.splitlines(keepends=True) if b'[R29D' not in l)
    assert recon == body, 'delete-stamps did not reconstruct the original bytes'
    print('%s: %d inserts, %d -> %d bytes, syntax ok, delete-stamps==original'
          % (rel, len(jobs), len(raw), len(after)))
