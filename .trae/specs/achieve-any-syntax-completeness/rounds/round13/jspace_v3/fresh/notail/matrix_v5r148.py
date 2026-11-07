# rr-v5r148 [v148-NOTTAIL] 变体矩阵 v2（A/B 单文件交换 + 判官字节验证）
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r148matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    'E1_ggo_tail': """def g(codes, n=3):
    group = []
    for tag in codes:
        group.append(tag)
    if group and not (len(group) == 1 and group[0] == 'equal'):
        yield group
""",
    'E2_twin_ret': """def g(a, b, c):
    if a and not (b and c):
        return None
    return None
""",
    'E3_ggo_real': """class SM:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def get_opcodes(self):
        return [('equal', 0, 1, 0, 1)]

    def get_grouped_opcodes(self, n=3):
        codes = self.get_opcodes()
        if not codes:
            codes = [('equal', 0, 1, 0, 1)]
        nn = n + n
        group = []
        for tag, i1, i2, j1, j2 in codes:
            if tag == 'equal' and i2 - i1 > nn:
                group.append((tag, i1, min(i2, i1 + n), j1, min(j2, j1 + n)))
                yield group
                group = []
                i1, j1 = (max(i1, i2 - n), max(j1, j2 - n))
            group.append((tag, i1, i2, j1, j2))
        if group and not (len(group) == 1 and group[0][0] == 'equal'):
            yield group
""",
    'C1_merged_exit': """def f(a, b, c):
    if a and not (b and c):
        x()
    return 0
""",
    'C2_ret1': """def f(a, b, c):
    if a and not (b and c):
        return 1
    return 0
""",
    'C3_tail3': """def f(a, b, c, d):
    if a and not (b and c and d):
        return 1
    return 0
""",
    'C4_k1': """def f(a, b):
    if a and not b:
        return 1
    return 0
""",
    'C5_notor': """def f(a, b, c):
    if a and not (b or c):
        return 1
    return 0
""",
    'C6_b116_nested': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
    'C7_b116_not': """def f(a, b):
    if a:
        if not b:
            return None
    return None
""",
    'C8_na5': """def f(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
""",
    'C9_orandtail': """def h(a, b, c):
    i = 0
    while i > 3 or b[i] and c[i]:
        i += 1
    return i
""",
    'C10_guard_nest': """def f(a, b, c, d):
    if a:
        while b and (c or d):
            b -= 1
    return b
""",
}

FILES = ('core/cfg/region_analyzer.py', 'core/cfg/region_ast_generator.py')


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
    import py_compile
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

    # B: v148 work tree
    write_files(WORK)
    prod_b = decompile(pyc, 'B', name)
    # A: HEAD (af3bc546)
    write_files(HEAD)
    prod_a = decompile(pyc, 'A', name)
    write_files(WORK)

    if prod_a is None or prod_b is None:
        print(name, 'DECOMP_FAIL')
        continue
    same = norm(prod_a) == norm(prod_b)
    status = 'SAME' if same else 'HEAD-TEXT-DIFF'
    # judge byte-verify on B product
    bp = os.path.join(OUT, '%s_B.py' % name)
    ok, fails = judge_equal(pyc, bp)
    bstat = 'JUDGE-EQUAL' if ok else 'JUDGE-DIFF:%s' % ';'.join(fails[:2])
    print('%-18s %-14s %s' % (name, status, bstat))
    if not same:
        print('  ---- A(HEAD) ----')
        for l in prod_a.splitlines():
            print('  ', l)
        print('  ---- B(v148) ----')
        for l in prod_b.splitlines():
            print('  ', l)
