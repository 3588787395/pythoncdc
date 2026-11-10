# rr-v5r158 [v158-RETFIN] 变体矩阵（A/B 交换：HEAD 7e3064cb vs v158 工作树）
# 功效案：try+finally 内联 return 值重组（if 臂穿 finally 正常路径副本）
# 控制案：try 体顶层 return（既有 B207/普通路径）/名形式 B75/无 finally/前轮家族
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r158matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    # ---- 功效案（HEAD-TEXT-DIFF → v158 JUDGE-EQUAL）----
    'E1_http302': """def fetch(self, meth, url, headers):
    self.tries += 1
    try:
        if self.maxtries and self.tries >= self.maxtries:
            if hasattr(self, 'http_error_500'):
                meth = self.http_error_500
            else:
                meth = self.http_error_default
            return meth(url, self, 500, 'Internal Server Error: Redirect Recursion', headers)
        result = self.redirect_internal(url, self)
        return result
    finally:
        self.tries = 0
""",
    'E2_min_call': """def f(self, g, x):
    try:
        if x:
            return g(x)
        return None
    finally:
        self.done = True
""",
    'E3_arith': """def f(self, a, b):
    try:
        if a > b:
            return a + b * 2
        return 0
    finally:
        self.n += 1
""",
    'E4_nested_call': """def f(self, g, h, x):
    try:
        if g(x):
            return h(g(x))
        return None
    finally:
        self.n = 0
""",
    'E5_attr': """def f(self, x):
    try:
        if x:
            return self.handler(x)
        return None
    finally:
        self.flag = False
""",
    'E6_two_stmt_finally': """def f(self, g, x):
    try:
        if x:
            return g(x)
        return None
    finally:
        self.n = 0
        self.done = True
""",
    'E7_else_arm': """def f(self, g, x):
    try:
        if x:
            self.mark(x)
        else:
            return g(x)
        return None
    finally:
        self.n = 0
""",
    # ---- 控制案（SAME 预期）----
    'C1_toplevel_return': """def f(self, g, x):
    try:
        return g(x)
    finally:
        self.n = 0
""",
    'C2_name_result': """def f(self, g, x):
    try:
        result = g(x)
        return result
    finally:
        self.n = 0
""",
    'C3_no_finally': """def f(g, x):
    if x:
        return g(x)
    return None
""",
    'C4_const_return': """def f(self, x):
    try:
        if x:
            return 0
        return 1
    finally:
        self.n = 0
""",
    'C5_handler_ret': """def f(it):
    while True:
        try:
            v = next(it)
        except StopIteration:
            return
        print(v)
""",
    'C6_kwmerge': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'C7_delwin': """def f(seq, flag):
    del seq[:]
    if flag:
        print(flag)
    return seq
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

FILES = ('core/cfg/region_ast_generator.py',)


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
        print('  ---- B(v158) ----')
        for l in prod_b.splitlines():
            print('  ', l)
