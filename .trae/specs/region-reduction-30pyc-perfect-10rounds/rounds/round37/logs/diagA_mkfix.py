# -*- coding: utf-8 -*-
"""Round37 diag A: build mirr_fix = landed mirror + candidate R37-A byte edit.

Anchor: core/cfg/region_ast_generator.py:16956-16961 (the `_or_elif_ir` ancestor
search inside `_if_generate_normal`).  Only change: an ancestor whose block set
already contains the CURRENT region's entry block is rejected as a candidate.

Usage: python -X utf8 mkfix.py
"""
import io
import os
import shutil
import sys

SRC = r'D:/Temp/r37diagA/mirr_probe'
DST = r'D:/Temp/r37diagA/mirr_fix'
GEN = os.path.join('core', 'cfg', 'region_ast_generator.py')

OLD = """            _or_elif_ir = None
            for r in self.region_analyzer.regions:
                if isinstance(r, IfRegion) and r.elif_conditions and r.then_blocks:
                    if any(b.start_offset == _r23_or_then.start_offset for b in r.then_blocks):
                        _or_elif_ir = r
                        break
"""

NEW = """            _or_elif_ir = None
            for r in self.region_analyzer.regions:
                if isinstance(r, IfRegion) and r.elif_conditions and r.then_blocks:
                    _r37_rb = set(getattr(r, 'blocks', None) or [])
                    if region.entry is not None and region.entry in _r37_rb:
                        continue        # [R37-A] an ancestor chain may not lend its elif arms
                    if any(b.start_offset == _r23_or_then.start_offset for b in r.then_blocks):
                        _or_elif_ir = r
                        break
"""

ANCHORS = [(OLD, NEW, 1)]


def main():
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('__pycache__'))
    p = os.path.join(DST, GEN)
    s = io.open(p, encoding='utf-8-sig', newline='').read()
    crlf = '\r\n' in s
    body = s.replace('\r\n', '\n')
    for old, new, want in ANCHORS:
        c = body.count(old)
        if c != want:
            print('ANCHOR-MISS (%d): %r' % (c, old[:70]))
            sys.exit(1)
        body = body.replace(old, new, 1)
    compile(body, 'mirr_fix region_ast_generator', 'exec')   # fail-fast on syntax
    if crlf:
        body = body.replace('\n', '\r\n')
    io.open(p, 'w', encoding='utf-8-sig', newline='').write(body)
    print('mirr_fix built. landed sha[:20]=%s  fixed bytes=%d (delta %+d)' % (
        __import__('hashlib').sha256(io.open(os.path.join(SRC, GEN), 'rb').read()).hexdigest()[:20],
        os.path.getsize(p), os.path.getsize(p) - os.path.getsize(os.path.join(SRC, GEN))))


if __name__ == '__main__':
    main()
