# rr-v5r153 [v153-RESIDUNPACK] 变体矩阵（A/B 单文件交换：HEAD 789e15b7 vs v153 工作树）
# 功效案：链式元组解包 `(a, b), (c, d) = x, y` 的六个语句位形（残栈值源族）
# 控制案：独立连续解包/嵌套解包/星号解包/walrus/属性目标/前轮家族 回归防护
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r153matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    'E1_toplevel': """def f1(x, y):
    (a, b), (c, d) = x, y
    return a + b + c + d
""",
    'E2_whilebody': """def f2(pairs):
    total = 0
    while total < len(pairs):
        (a, b), (c, d) = pairs[total], pairs[total + 1]
        total += a + b + c + d
    return total
""",
    'E3_forbody': """def f3(pairs):
    out = []
    for p in pairs:
        (a, b), (c, d) = p, p
        out.append(a + b + c + d)
    return out
""",
    'E4_ifbody': """def f4(x, y):
    if x:
        (a, b), (c, d) = x, y
    return (a, b, c, d)
""",
    'E5_ifelse_seq': """def f5(x, y):
    if x:
        t = 1
    else:
        t = 2
    (a, b), (c, d) = x, y
    return a + b + c + d + t
""",
    'E6_after_while': """def f6(xs):
    i = 0
    while i < len(xs):
        i += 1
    (a, b), (c, d) = xs[0], xs[1]
    return a + b + c + d
""",
    'C1_indep': """def f(xs, ys):
    a, b = xs
    c, d = ys
    return a + b + c + d
""",
    'C2_single': """def f(xs):
    a, b = xs
    return a + b
""",
    'C3_nested': """def f(x):
    a, (b, c) = x
    return a + b + c
""",
    'C4_starred': """def f(xs):
    a, *b = xs
    return (a, b)
""",
    'C5_walrus': """def f(g):
    a, b = (d := g())
    return a + b + d
""",
    'C6_attr_target': """class R:
    def __init__(self, f):
        self.conn, self.cur = f()
""",
    'C7_subscr_target': """def f(d, g):
    d['x'], d['y'] = g()
    return d
""",
    'C8_mdiff3': """def gen(line_iterator):
    fromlines, tolines = [], []
    while True:
        while (len(fromlines) == 0 or len(tolines) == 0):
            try:
                from_line, to_line, found_diff = next(line_iterator)
            except StopIteration:
                return
            if from_line is not None:
                fromlines.append((from_line, found_diff))
            if to_line is not None:
                tolines.append((to_line, found_diff))
        from_line, fromDiff = fromlines.pop(0)
        to_line, to_diff = tolines.pop(0)
        yield (from_line, to_line, fromDiff or to_diff)
""",
    'C9_latch_if': """def gen(diffs):
    for fromdata, todata, flag in diffs:
        fromlist, tolist = [], []
        while fromlist or tolist:
            if fromlist:
                fromdata = fromlist.pop(0)
            else:
                fromdata = ('', ' ')
            if tolist:
                todata = tolist.pop(0)
            else:
                todata = ('', ' ')
            yield (fromdata, todata, flag)
""",
    'C10_line_wrapper_real': """class HtmlDiff:
    _default_prefix = 0

    def _split_line(self, lines, line, text):
        pass

    def _line_wrapper(self, diffs):
        for fromdata, todata, flag in diffs:
            if flag is None:
                yield (fromdata, todata, flag)
                continue
            (fromline, fromtext), (toline, totext) = fromdata, todata
            fromlist, tolist = [], []
            self._split_line(fromlist, fromline, fromtext)
            self._split_line(tolist, toline, totext)
            while fromlist or tolist:
                if fromlist:
                    fromdata = fromlist.pop(0)
                else:
                    fromdata = ('', ' ')
                if tolist:
                    todata = tolist.pop(0)
                else:
                    todata = ('', ' ')
                yield (fromdata, todata, flag)
""",
    'C11_fancy_tail': """def _fancy_helper(a, alo, ahi, b, blo, bhi):
    yield ('h',)


def fancy_tail(a, b, best_i, best_j, cruncher):
    eqi = None
    yield from _fancy_helper(a, 0, best_i, b, 0, best_j)
    aelt, belt = a[best_i], b[best_j]
    if eqi is None:
        atags = btags = ''
        cruncher.set_seqs(aelt, belt)
        for tag, ai1, ai2, bj1, bj2 in cruncher.get_opcodes():
            la, lb = ai2 - ai1, bj2 - bj1
            if tag == 'replace':
                atags += '^' * la
                btags += '^' * lb
            elif tag == 'equal':
                atags += ' ' * la
                btags += ' ' * lb
            else:
                raise ValueError('unknown tag')
    else:
        yield '  ' + aelt
    yield from _fancy_helper(a, best_i + 1, 9, b, best_j + 1, 9)
""",
    'C12_na5': """def f(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
""",
    'C13_b116': """def f(a, b):
    if a:
        if b:
            return None
    return None
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
        print('  ---- B(v153) ----')
        for l in prod_b.splitlines():
            print('  ', l)
