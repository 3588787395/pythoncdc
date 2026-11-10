# rr-v5r156 [v156-BINPAREN] 变体矩阵（A/B 交换：HEAD 4a2208e6 vs v156 工作树）
# 功效案：BinOp 同优先级右子括号（tarfile.close 实形 NUL * (BLOCKSIZE * 2)）
# 控制案：左嵌套/除法既有集/幂右结合/低优先级右子/前轮家族
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r156matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    # ---- 功效案（HEAD-TEXT-DIFF → v156 JUDGE-EQUAL）----
    'E1_close': """def f(fileobj, NUL, BLOCKSIZE):
    fileobj.write(NUL * (BLOCKSIZE * 2))
    fileobj.write(NUL * (BLOCKSIZE * 3))
""",
    'E2_mul_minimal': """def f(a, b):
    return a * (b * 2)
""",
    'E3_add': """def f(a, b, c):
    return a + (b + c)
""",
    'E4_cross_mul_div': """def f(a, b, c):
    return a * (b / c)
""",
    'E5_cross_add_sub': """def f(a, b, c):
    return a + (b - c)
""",
    'E6_shift': """def f(a, b, c):
    return a << (b << c)
""",
    'E7_bitwise': """def f(a, b, c):
    return a | (b | c)
""",
    'E8_in_call_arg': """def f(a, b, c):
    return g(a % (b % c), a - (b % c))
""",
    # ---- 控制案（SAME 预期）----
    'C1_left_nested': """def f(a, b, c):
    return a * b * c
""",
    'C2_div_legacy': """def f(a, b, c):
    return a - (b - c)
""",
    'C3_power_right': """def f(a, b, c):
    return a ** (b ** c)
""",
    'C4_lower_prec_right': """def f(a, b, c):
    return a * (b + c)
""",
    'C5_paren_left': """def f(a, b, c):
    return (a + b) * c
""",
    'C6_kwmerge': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'C7_dual_unpack': """def f(x, y):
    (a, b), (c, d) = x, y
    return a + b + c + d
""",
    'C8_cfo2': """def f(src, dst, length=None, bufsize=None):
    bufsize = bufsize or 16 * 1024
    if length == 0:
        return
    print(bufsize, length)
""",
    'C9_b116': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
}

FILES = ('core/cfg/code_generator.py',)


def norm(t):
    lines = [l.rstrip() for l in t.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return '\n'.join(lines)


def read_work():
    return {f: open(os.path.join(REPO, f), 'rb').read() for f in FILES}


def write_files(content_map):
    for f, content in content_map.items():
        open(os.path.join(REPO, f), 'wb').write(content)


def git_show_head(f):
    r = subprocess.run(['git', '-C', REPO, 'show', 'HEAD:%s' % f],
                       capture_output=True, check=True)
    return r.stdout


def decompile(pyc, tag, name):
    out = os.path.join(OUT, '%s_%s.py' % (name, tag))
    r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', pyc, '-o', out],
                       capture_output=True, cwd=REPO, timeout=180)
    if not os.path.isfile(out):
        return None
    return open(out, encoding='utf-8').read()


def judge_equal(orig_pyc, prod_py):
    sys.path.insert(0, REPO)
    if not hasattr(typing, 'override'):
        typing.override = lambda func: func
    if 'pydot' not in sys.modules:
        stub = types.ModuleType('pydot')
        stub.graph_from_dot_data = lambda *a, **k: []
        stub.Dot = stub.Node = stub.Edge = lambda *a, **k: None
        sys.modules['pydot'] = stub
    if 'pylingual' not in sys.modules:
        pkg = types.ModuleType('pylingual')
        pkg.__path__ = [r'D:/Desktop/ptrade相关/pylingual/pylingual']
        sys.modules['pylingual'] = pkg
    from pylingual.equivalence_check import compare_pyc
    rec = orig_pyc.replace('.pyc', '_rec.pyc')
    try:
        py_compile.compile(prod_py, cfile=rec, doraise=True)
        results = compare_pyc(orig_pyc, rec)
        return all(r.success for r in results), [str(getattr(r, 'message', r)) for r in results if not r.success]
    except Exception as e:
        return False, ['compile_error: %s' % e]


WORK = read_work()
HEAD = {f: git_show_head(f) for f in FILES}

print('==== SUMMARY ====')
for name, src in CASES.items():
    sp = os.path.join(OUT, name + '_src.py')
    open(sp, 'w', encoding='utf-8').write(src)
    pyc = os.path.join(OUT, name + '.pyc')
    py_compile.compile(sp, cfile=pyc, doraise=True)

    write_files(WORK)
    prod_b = decompile(pyc, 'B', name)
    write_files(HEAD)
    prod_a = decompile(pyc, 'A', name)
    write_files(WORK)

    if prod_a is None or prod_b is None:
        print(name, 'DECOMP_FAIL')
        continue
    same = norm(prod_a) == norm(prod_b)
    status = 'SAME' if same else 'HEAD-TEXT-DIFF'
    bp = os.path.join(OUT, '%s_B.py' % name)
    ok, fails = judge_equal(pyc, bp)
    bstat = 'JUDGE-EQUAL' if ok else 'JUDGE-DIFF:%s' % ';'.join(fails[:2])
    print('%-24s %-14s %s' % (name, status, bstat))
    if not same:
        print('  ---- A(HEAD) ----')
        for l in prod_a.splitlines():
            print('  ', l)
        print('  ---- B(v156) ----')
        for l in prod_b.splitlines():
            print('  ', l)
