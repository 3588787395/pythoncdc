# rr-v5r159 [v159-NOTCOND] 变体矩阵（A/B 交换：HEAD 7758884f vs v159 工作树）
# 功效案：前置赋值 + CONTAINS_OP 成员测试 FALSE 模式 BoolOp 链启动
# （HTTPRedirectHandler.redirect_request 实形 not(A∧B∨C∧D) 语义反转）
# 控制案：无前置赋形/TRUE 模式 R38/COMPARE 链排除域/简单变量窗/前轮家族
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r159matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    # ---- 功效案（HEAD-TEXT-DIFF → v159 JUDGE-EQUAL）----
    'E1_rr': """class Handler:
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        m = req.get_method()
        if (not (code in (301, 302, 303, 307, 308) and m in ('GET', 'HEAD')
                 or code in (301, 302, 303) and m == 'POST')):
            raise ValueError(req.full_url, code, msg, headers, fp)
        newurl = newurl.replace(' ', '%20')
        return newurl
""",
    'E2_preassign_and': """def f(x, T, y):
    x = prep(x)
    if x in T and y:
        print(x, y)
    return x
""",
    'E3_not_mixed': """def f(x, T, y, z):
    x = prep(x)
    if not (x in T and y or z == 'P'):
        raise ValueError(x, y, z)
    return x
""",
    'E4_not_single': """def f(x, T, y):
    x = prep(x)
    if not (x in T and y):
        raise ValueError(x, y)
    return x
""",
    'E5_two_preassign': """def f(a, T, b):
    a = prep(a)
    b = prep2(b)
    if not (a in T and b or a == 2):
        raise ValueError(a, b)
    return a, b
""",
    'E6_precall_shape': """def f(code, m, req, fp, newurl):
    m = req.get_method()
    if (not (code in (301, 302, 303, 307, 308) and m in ('GET', 'HEAD')
             or code in (301, 302, 303) and m == 'POST')):
        raise ValueError(req.full_url, code, m)
    return newurl
""",
    # ---- 控制案（SAME 预期）----
    'C1_no_preassign': """def f(code, m):
    if (not (code in (301, 302, 303, 307, 308) and m in ('GET', 'HEAD')
             or code in (301, 302, 303) and m == 'POST')):
        raise ValueError(code, m)
    return code
""",
    'C2_true_mode': """def f(x, T, y):
    x = prep(x)
    if x in T or y:
        print(x, y)
    return x
""",
    'C3_compare': """def f(x, y, z):
    x = prep(x)
    if x == (y or z):
        print(x)
    return x
""",
    'C4_simple_var': """def f(x, y):
    x = prep(x)
    if x and y:
        print(x, y)
    return x
""",
    'C5_kwmerge': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'C6_delwin': """def f(seq, flag):
    del seq[:]
    if flag:
        print(flag)
    return seq
""",
    'C7_retfin': """def f(self, g, x):
    try:
        if x:
            return g(x)
        return None
    finally:
        self.done = True
""",
    'C8_binparen': """def f(a, b):
    return a * (b * 2)
""",
    'C9_b116': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
}

FILES = ('core/cfg/region_analyzer.py',)


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
        print('  ---- B(v159) ----')
        for l in prod_b.splitlines():
            print('  ', l)
