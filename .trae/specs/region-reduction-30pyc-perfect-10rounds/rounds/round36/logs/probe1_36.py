# -*- coding: utf-8 -*-
"""Round 36 read-only probe #1: characterise one defective function in the landed bytes.

  python -X utf8 probe1_36.py <pyc relpath under site-packages> <function name>

Prints the official ruler's mismatch record for that function, the strict ruler's opcode hunks
(filtered token sequences, jumps compared as `<JUMP> kind`), the surrounding instruction window of
each hunk on both sides, and the product text of the function. Nothing in the repo is written; the
recompiled product goes to this scratch dir under an explicit cfile.
"""
import difflib
import importlib.util
import io
import json
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r36gate/r36'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
_b = importlib.util.spec_from_file_location('pbv', os.path.join(REPO, 'scripts', 'pyc_batch_verify.py'))
pbv = importlib.util.module_from_spec(_b)
_b.loader.exec_module(pbv)

rel = sys.argv[1].replace('/', os.sep)
NAME = sys.argv[2]
PYC = os.path.join(REPO, 'site-packages', rel)
PY = PYC[:-4] + 'OK.py'
assert os.path.isfile(PYC), PYC
assert os.path.isfile(PY), PY

L = []
r = pbv.bytecode_diff(PYC, PY)
L.append('official  %s/%s   product %s' % (r.get('matched_functions'), r.get('total_functions'),
                                           os.path.basename(PY)))
for m in (r.get('mismatches') or []):
    L.append('  mismatch %-46s orig=%s decomp=%s jump=%s true=%s' % (
        m.get('name'), m.get('orig_count'), m.get('decomp_count'),
        m.get('jump_diffs'), m.get('true_diffs')))
    fd = m.get('first_diff')
    L.append('    first_diff %s' % json.dumps(fd, ensure_ascii=False)[:600])

cfile = os.path.join(ROOT, 'probe1_' + os.path.basename(PY)[:-3] + '.pyc')
py_compile.compile(PY, cfile=cfile, doraise=True, quiet=2)


def pick(mp):
    k = [q for q in mp if q.split('.')[-1] == NAME]
    assert k, 'no %s in %s' % (NAME, sorted(mp)[:5])
    return mp[k[0]]


o = pick(r10._load_map(PYC))
d = pick(r10._load_map(cfile))
kind, msg, is_defect = r10.strict_compare(o, d)
fo, fd2 = r10.filtered(o), r10.filtered(d)
L.append('\nstrict   kind=%r defect=%r msg=%r  lo=%d ld=%d delta=%+d'
         % (kind, is_defect, msg, len(fo), len(fd2), len(fd2) - len(fo)))


def tok(x):
    if r10._is_jump(x.opname):
        return ('<JUMP>', r10._norm_jump_op(x.opname))
    return (r10._norm_arg(x), x.opname)


to, td = [tok(x) for x in fo], [tok(x) for x in fd2]
L.append('\n== hunks (non-equal only) ==')
for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, to, td, autojunk=False).get_opcodes():
    if t == 'equal':
        continue
    L.append('  %-8s orig[%d:%d] @%d..%d -> decomp[%d:%d] @%s..%s' % (
        t, i1, i2, fo[i1].offset, fo[i2 - 1].offset, j1, j2,
        fd2[j1].offset if j1 < len(fd2) else '-', fd2[j2 - 1].offset if j2 > 0 else '-'))
    L.append('      orig  %s' % [x[1] for x in to[i1:i2]])
    L.append('      decomp %s' % [x[1] for x in td[j1:j2]])
    L.append('      orig args %s' % [(x[1], x[0] if not isinstance(x[0], str) else x[0][:24])
                                     for x in to[max(0, i1 - 3):i2 + 3]])
    L.append('      decp args %s' % [(x[1], x[0] if not isinstance(x[0], str) else x[0][:24])
                                     for x in td[max(0, j1 - 3):j2 + 3]])

text = io.open(PY, encoding='utf-8-sig').read().replace('\r\n', '\n').split('\n')
start = None
for k, l in enumerate(text):
    if l.strip().startswith('def %s(' % NAME):
        start = k
        break
if start is not None:
    ind = len(text[start]) - len(text[start].lstrip())
    end = start
    for j in range(start + 1, len(text)):
        if text[j].strip():
            if (len(text[j]) - len(text[j].lstrip())) <= ind:
                break
            end = j
    L.append('\n== product text %s lines %d..%d (def indent %d) ==' % (NAME, start + 1, end + 1, ind))
    for k in range(start, end + 1):
        L.append('%4d|%s' % (k + 1, text[k]))

out = os.path.join(ROOT, 'probe1_%s_%s.txt' % (os.path.splitext(os.path.basename(rel))[0], NAME))
io.open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
print('\n'.join(L[:40]))
print('... wrote %s (%d lines)' % (out.replace('\\', '/'), len(L)))
