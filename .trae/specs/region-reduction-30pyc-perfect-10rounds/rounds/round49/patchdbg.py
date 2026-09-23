# -*- coding: utf-8 -*-
"""Add header/then/else offsets to the two merge-fallback debug prints."""
import io

P = r'D:/Temp/r49mine/dbgcore/core/cfg/region_analyzer.py'
u = io.open(P, encoding='utf-8-sig', newline='').read()
nl = '\r\n' if u.count('\r') else '\n'
u = u.replace(nl, '\n')
for tag in ['17012', '17055']:
    a = "print('R49HIT@" + tag + "', merge.start_offset"
    assert u.count(a) == 1, tag
    b = ("print('R49HIT@" + tag + "', 'H=' + str(getattr(block, 'start_offset', None))"
         " + ' T=' + str(getattr(then_succ, 'start_offset', None))"
         " + ' E=' + str(getattr(else_succ, 'start_offset', None)),"
         " merge.start_offset")
    u = u.replace(a, b)
io.open(P, 'w', encoding='utf-8-sig', newline='').write(u.replace('\n', nl))
print('patched')
