# -*- coding: utf-8 -*-
"""R35 read-only probe #1: land the target function's product text next to the original
bytecode tail, and show what the strict ruler reports as missing.

Writes nothing into the repo.
"""
import importlib.util
import io
import json
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/r35gate/r35'
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

PYC = REPO + '/site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc'
PY = REPO + '/site-packages/IQEngine/plugins/plugin_system_risk_calculation/functionOK.py'
NAME = 'save_testds_to_json'

def compile_map(py):
    cfile = os.path.join(OUT, 'probe1_' + os.path.basename(py).replace('.py', '') + '.pyc')
    py_compile.compile(py, cfile=cfile, doraise=True, quiet=2)
    return r10._load_map(cfile)


o = r10._load_map(PYC)[[k for k in r10._load_map(PYC) if k.split('.')[-1] == NAME][0]]
d = compile_map(PY)[[k for k in compile_map(PY) if k.split('.')[-1] == NAME][0]]

lines = []
kind, msg, is_defect = r10.strict_compare(o, d)
lines.append('strict: kind=%r defect=%r  lo=%d ld=%d' % (kind, is_defect, len(r10.filtered(o)), len(r10.filtered(d))))

# --- original tail: last 30 filtered instructions
fo = r10.filtered(o)
fd = r10.filtered(d)
lines.append('\n== orig filtered tail (last 22) ==')
for i in fo[-22:]:
    lines.append('  @%-5d %s %s' % (i.offset, i.opname, i.argval if i.opname.startswith('LOAD') else ''))
lines.append('== decomp filtered tail (last 14) ==')
for i in fd[-14:]:
    lines.append('  @%-5d %s %s' % (i.offset, i.opname, i.argval if i.opname.startswith('LOAD') else ''))

# --- the missing segment per difflib, exactly as the strict hunk reports it
import difflib


def tok(x):
    if r10._is_jump(x.opname):
        return ('<JUMP>', r10._norm_jump_op(x.opname))
    return (r10._norm_arg(x), x.opname)


to, td = [tok(x) for x in fo], [tok(x) for x in fd]
lines.append('\n== opcodes (orig vs decomp), non-equal only ==')
for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, to, td, autojunk=False).get_opcodes():
    if t == 'equal':
        continue
    lines.append('  %-8s orig[%d:%d] @%d..%d -> decomp[%d:%d]  %s | %s' % (
        t, i1, i2, fo[i1].offset, fo[i2 - 1].offset, j1, j2,
        [x[1] for x in to[i1:i2]], [x[1] for x in td[j1:j2]]))

# --- product text of the function
text = io.open(PY, encoding='utf-8-sig').read().replace('\r\n', '\n').split('\n')
start = None
for k, l in enumerate(text):
    if l.strip().startswith('def %s(' % NAME):
        start = k
        break
ind = len(text[start]) - len(text[start].lstrip())
end = start
for j in range(start + 1, len(text)):
    if text[j].strip():
        if (len(text[j]) - len(text[j].lstrip())) <= ind:
            break
        end = j
lines.append('\n== product text %s : lines %d..%d (def indent %d) ==' % (NAME, start + 1, end + 1, ind))
for k in range(start, end + 1):
    lines.append('%4d|%s' % (k + 1, text[k]))

io.open(os.path.join(OUT, 'probe1_target.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print('\n'.join(lines[:6]))
print('wrote probe1_target.txt', len(lines), 'lines')
