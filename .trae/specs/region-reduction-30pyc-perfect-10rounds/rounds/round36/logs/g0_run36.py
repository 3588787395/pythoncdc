# -*- coding: utf-8 -*-
"""Round 36 G0 runner: measure the seven shapes on a given core arm (default = LANDED repo core).

Per shape we print
  official   m/n from scripts/pyc_batch_verify.bytecode_diff, plus the per-function mismatch row
  strict     kind + lo/ld/delta + the non-equal hunks over filtered (opname, norm-arg) tokens
  product    the emitted text of function `f` (what actually survived)

G0 criterion: the WITNESS shapes (r36_01/02) must FAIL on landed bytes and every CONTROL must
PASS.  A control that fails means the drop is not specific to the target shape, so the target
claim (and any predicate derived from it) has to be re-scoped.

usage: python -X utf8 g0_run36.py [arm-dir] [report-name]
"""
import difflib
import importlib.util
import io
import os
import py_compile
import sys

REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/r36gate/r36'
DST = REPO + '/test_repros/round36_for_loop_dropped'
CORE = sys.argv[1] if len(sys.argv) > 1 else REPO
TAG = sys.argv[2] if len(sys.argv) > 2 else 'landed'
sys.stdout.reconfigure(encoding='utf-8')

_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
_bv = importlib.util.spec_from_file_location('pbv', REPO + '/scripts/pyc_batch_verify.py')
pbv = importlib.util.module_from_spec(_bv)
_bv.loader.exec_module(pbv)
sys.path.insert(0, CORE)
import pycdc  # noqa: E402
assert os.path.dirname(os.path.abspath(pycdc.__file__)).replace('\\', '/') == CORE.replace('\\', '/'), \
    'pycdc resolved to the wrong arm'


def tok(i):
    if r10._is_jump(i.opname):
        return ('<JUMP>', r10._norm_jump_op(i.opname))
    return (r10._norm_arg(i), i.opname)


def body(txt, name):
    lines = txt.split('\n')
    out, on = [], False
    for l in lines:
        if l.startswith('def %s(' % name):
            on = True
        elif on and l and not l.startswith((' ', '\t', ')')):
            break
        if on:
            out.append(l)
    return out


rep = ['CORE=%s' % CORE]
npass = 0
for name in sorted(os.listdir(DST)):
    if not name.endswith('.pyc'):
        continue
    stem = name[:-4]
    pyc = os.path.join(DST, name)
    prod = os.path.join(OUT, 'g0_%s_%s.py' % (stem, TAG))
    if os.path.isfile(prod):
        os.remove(prod)
    pbv.decompile_single(pyc, prod)
    res = pbv.bytecode_diff(pyc, prod)
    ok_official = res['matched_functions'] == res['total_functions']
    tmp = os.path.join(OUT, 'g0c_%s_%s.pyc' % (stem, TAG))
    py_compile.compile(prod, cfile=tmp, doraise=True, quiet=2)
    o, d = r10._load_map(pyc), r10._load_map(tmp)
    hunk_lines, strict_bad = [], []
    for k in sorted(o):
        if k not in d:
            strict_bad.append('%s MISSING' % k)
            continue
        kind, msg, defect = r10.strict_compare(o[k], d[k])
        fo, fd = r10.filtered(o[k]), r10.filtered(d[k])
        if defect:
            strict_bad.append('%s %s lo=%d ld=%d delta%+d' % (k.split('.')[-1], kind, len(fo),
                                                              len(fd), len(fd) - len(fo)))
        for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [tok(x) for x in fo],
                                                         [tok(x) for x in fd],
                                                         autojunk=False).get_opcodes():
            if t != 'equal':
                hunk_lines.append('      hunk %s %s[%d:%d]@%s %s -> %s[%d:%d]@%s %s' % (
                    t, k.split('.')[-1], i1, i2, fo[i1].offset if i1 < len(fo) else 'EOF',
                    [x.opname for x in fo[i1:i2]], k.split('.')[-1], j1, j2,
                    fd[j1].offset if j1 < len(fd) else 'EOF', [x.opname for x in fd[j1:j2]]))
    ok = ok_official and not strict_bad
    npass += 1 if ok else 0
    rows = ['%s %d/%d' % (m['name'], m['orig_count'], m['decomp_count'])
            for m in res['mismatches']]
    rep.append('%-52s %s  official %d/%d  strict %s %s' % (
        stem, 'PASS' if ok else 'FAIL', res['matched_functions'], res['total_functions'],
        'ok' if not strict_bad else '; '.join(strict_bad), ('| ' + ', '.join(rows)) if rows else ''))
    for h in hunk_lines:
        rep.append(h)
    for l in body(io.open(prod, encoding='utf-8-sig').read(), 'f'):
        rep.append('      | ' + l)
rep.append('PASS %d / %d' % (npass, len([x for x in os.listdir(DST) if x.endswith('.pyc')])))
io.open(os.path.join(OUT, 'g0_%s.txt' % TAG), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(rep) + '\n')
print('\n'.join(rep))
