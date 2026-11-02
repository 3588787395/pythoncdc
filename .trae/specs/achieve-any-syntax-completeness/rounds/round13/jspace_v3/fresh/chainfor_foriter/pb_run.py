# Family-B (StrEnum.__new__ elif-merge not-loss) repro runner:
#   compile src -> pyc -> decompile via HEAD pycdc.py -> recompile both -> compare
import os, sys, subprocess, types, marshal, py_compile

REPO = 'F:/Downloads/pythoncdc-main'
R98 = 'D:/temp/opencode/cl_layout/r98'

def norm(c):
    return (c.co_code.hex(), c.co_exceptiontable.hex(),
            c.co_names, c.co_varnames, c.co_freevars, c.co_cellvars,
            tuple(norm(k) if isinstance(k, types.CodeType) else k for k in c.co_consts))

def toplevels(c):
    out = {}
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            out[k.co_name] = norm(k)
    return out

def load(pyc):
    with open(pyc, 'rb') as f:
        return marshal.loads(f.read()[16:])

def compile_src(src, pyc):
    py_compile.compile(src, pyc, doraise=True)
    return load(pyc)

def run_case(name, srcpath):
    pyc = R98 + f'/{name}.pbpyc'
    out = R98 + f'/{name}_out.py'
    ca = toplevels(compile_src(srcpath, pyc))
    with open(out, 'wb') as fo, open(R98 + f'/{name}_err.txt', 'wb') as fe:
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', REPO + '/pycdc.py', pyc],
                           stdout=fo, stderr=fe, cwd=REPO, timeout=120)
    if r.returncode != 0:
        print(name, 'DECOMPILE-FAIL rc=%d' % r.returncode)
        return False
    cb = toplevels(compile_src(out, pyc + '.b'))
    if ca == cb:
        print(name, 'BYTE-EQUAL')
        return True
    print(name, 'DIFF fns=%s' % sorted(set(ca) | set(cb)))
    for fn in sorted(set(ca) | set(cb)):
        a, b = ca.get(fn), cb.get(fn)
        if a != b:
            print('  diff-in:', fn)
            if a and b and a[0] != b[0]:
                print('    co_code A=%s...' % a[0][:120])
                print('    co_code B=%s...' % b[0][:120])
    return False

ok = True
for name in sys.argv[1:]:
    if not run_case(name, R98 + f'/{name}.py'):
        ok = False
sys.exit(0 if ok else 1)
