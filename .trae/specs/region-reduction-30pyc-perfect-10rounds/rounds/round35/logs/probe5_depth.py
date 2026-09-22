# -*- coding: utf-8 -*-
"""R35 read-only probe #5 (rewrite): the depth ladder + trailing-code control for the
handler-tail `return None` law.

gen(d) builds `d` nested try/except statements -- each try's handler body contains the next
try -- and puts `return None` as the last statement of the INNERMOST handler, so the number
of active exception-handler scopes at that return is exactly d.  For each shape we compare
the compiled instruction sequence with and without that return.
"""
import difflib
import dis
import io
import os
import sys

OUT = r'D:/Temp/r35gate/r35'
sys.stdout.reconfigure(encoding='utf-8')


def gen(d, indent=1):
    ind = '    ' * indent
    lines = [ind + 'try:', ind + '    g(a)', ind + 'except BaseException:', ind + '    k(a)']
    if d > 1:
        lines += gen(d - 1, indent + 1)
    else:
        lines.append(ind + '    return None')
    return lines


def src(d, trailing):
    body = ['def f(a):'] + gen(d)
    if trailing:
        body.append('    z(a)')
    return '\n'.join(body) + '\n'


def code(s):
    ns = {'g': lambda *a: None, 'k': lambda *a: None, 'z': lambda *a: None}
    exec(compile(s, '<s>', 'exec'), ns)
    return [i.opname for i in dis.get_instructions(ns['f']) if i.opname != 'CACHE']


rep = []
for trailing in (False, True):
    for d in range(1, 6):
        s_with = src(d, trailing)
        s_without = '\n'.join(l for l in s_with.split('\n') if l.strip() != 'return None') + '\n'
        sw, swo = code(s_with), code(s_without)
        diff = []
        for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, sw, swo, autojunk=False).get_opcodes():
            if t != 'equal':
                diff.append('%s with=%s without=%s' % (t[0] + 'i' if t == 'insert' else t,
                                                       sw[i1:i2], swo[j1:j2]))
        rep.append('depth=%d trailing=%-5s with=%3d without=%3d identical=%-5s  %s' % (
            d, trailing, len(sw), len(swo), sw == swo, ' | '.join(diff)[:170]))
io.open(os.path.join(OUT, 'probe5_depth.txt'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(rep) + '\n')
print('\n'.join(rep))
