# -*- coding: utf-8 -*-
"""R35 read-only probe #4: the source->bytecode LAW behind the target's :367 line.

No decompiler involved.  For each shape we compile two variants -- with and without the
trailing `return None` of an except-handler -- and report whether the emitted instruction
sequence differs, and by which instructions.  The point is to learn which *structural*
fact decides whether a handler-tail `return None` is materialised by the compiler as a
separate epilogue or shared with the function's implicit return.
"""
import dis
import io
import os
import sys

OUT = r'D:/Temp/r35gate/r35'
sys.stdout.reconfigure(encoding='utf-8')

SHAPES = {}

# S1: nested handler tail; the try statement is the last thing in every enclosing scope.
SHAPES['S1_nested_handler_tail'] = """
def f(a):
    try:
        g(a)
    except BaseException:
        try:
            h(a)
        except BaseException:
            k(a)
{RET12}
"""

# S2: same, but a statement follows the outer try -> the handler's fall-through is not the end.
SHAPES['S2_nested_then_tail_code'] = """
def f(a):
    try:
        g(a)
    except BaseException:
        try:
            h(a)
        except BaseException:
            k(a)
{RET12}
    z(a)
"""

# S3: single (non-nested) handler tail.
SHAPES['S3_one_handler_tail'] = """
def f(a):
    try:
        g(a)
    except BaseException:
        k(a)
{RET8}
"""

# S4: return at the end of a TRY BODY (the target's :345/:353 shape).
SHAPES['S4_trybody_tail'] = """
def f(a):
    try:
        g(a)
{RET8}    except BaseException:
        k(a)
    z(a)
"""

# S5: three-deep handler tails (the target's actual depth).
SHAPES['S5_three_deep'] = """
def f(a):
    try:
        g(a)
{RET8}    except BaseException:
        try:
            h(a)
{RET12}        except BaseException:
            try:
                m(a)
            except BaseException:
                k(a)
{RET12}
"""

MODS = {'g': 1, 'h': 1, 'k': 1, 'm': 1, 'z': 1}
lines = []


def seq_of(fn):
    return ['%s' % i.opname for i in dis.get_instructions(fn) if i.opname != 'CACHE']


def emit(src, tag):
    ns = dict(MODS)
    exec(compile(src, '<%s>' % tag, 'exec'), ns)
    return ns['f']


report = []
for name, tpl in SHAPES.items():
    with_none = tpl.format(RET8='        return None\n', RET12='            return None\n')
    without = tpl.format(RET8='', RET12='')
    f_w, f_wo = emit(with_none, name + '_with'), emit(without, name + '_without')
    sw, swo = seq_of(f_w), seq_of(f_wo)
    report.append('%-28s with=%3d  without=%3d  identical=%s' % (name, len(sw), len(swo), sw == swo))
    if sw != swo:
        import difflib
        for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, sw, swo, autojunk=False).get_opcodes():
            if t != 'equal':
                report.append('      %-7s with[%d:%d]=%s  without[%d:%d]=%s' % (
                    t, i1, i2, sw[i1:i2], j1, j2, swo[j1:j2]))
io.open(os.path.join(OUT, 'probe4_law.txt'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(report) + '\n')
print('\n'.join(report))
