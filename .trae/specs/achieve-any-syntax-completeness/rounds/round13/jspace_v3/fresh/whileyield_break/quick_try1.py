# rr-v5r113 第一次窄改快速验证：r1/r2/r3/r4 compile->pyc->pycdc->recompile->BYTE-EQUAL
import os, subprocess, py_compile, marshal, types
REPO = 'F:/Downloads/pythoncdc-main'
MP = 'D:/temp/opencode/cl_layout/r113matrix'
REPRO = 'D:/temp/opencode/cl_layout/r112diag_a/repro'
PY = 'D:/Python/python.exe'
PYCDC = REPO + '/pycdc.py'
os.makedirs(MP, exist_ok=True)
CASES = ['r1_while_yield_break', 'r2_while_yield_preinit',
         'r3_while_yield_no_break', 'r4_exact_shape']


def norm(c):
    return (c.co_code.hex(), c.co_exceptiontable.hex(),
            c.co_names, c.co_varnames, c.co_freevars, c.co_cellvars, c.co_flags,
            tuple(norm(k) if isinstance(k, types.CodeType) else k for k in c.co_consts))


def flat(c, prefix=''):
    out = {prefix + c.co_name: c}
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            out.update(flat(k, prefix + c.co_name + '.'))
    return out


def load(p):
    with open(p, 'rb') as f:
        return marshal.loads(f.read()[16:])


for name in CASES:
    src = open(REPRO + '/%s.py' % name, encoding='utf-8').read()
    sp = MP + '/%s.py' % name
    pyc = MP + '/%s.pyc' % name
    pp = MP + '/%s_prod.py' % name
    ppe = MP + '/%s_prod.py.err' % name
    open(sp, 'w', encoding='utf-8').write(src)
    py_compile.compile(sp, pyc, doraise=True)
    ca = {n: norm(c) for n, c in flat(load(pyc)).items()}
    with open(pp, 'wb') as fo, open(ppe, 'wb') as fe:
        r = subprocess.run([PY, '-I', '-X', 'utf8', PYCDC, pyc],
                           stdout=fo, stderr=fe, cwd=REPO, timeout=300)
    txt = open(pp, encoding='utf-8').read()
    try:
        cb = {n: norm(c) for n, c in flat(compile(txt, 'p', 'exec')).items()}
        be = ca == cb
        detail = '' if be else 'rem=%s add=%s chg=%s' % (
            sorted(set(ca) - set(cb)), sorted(set(cb) - set(ca)),
            sorted(n for n in set(ca) & set(cb) if ca[n] != cb[n]))
    except SyntaxError as se:
        be, detail = False, 'SYNTAX-ERR ' + se.msg[:50]
    print('==== %s  rc=%s BYTE-EQUAL=%s %s' % (name, r.returncode, be, detail))
    print('  has_while=%s has_yield=%s' % ('while ' in txt, 'yield' in txt))
    for l in txt.splitlines():
        print('    | ' + l)
