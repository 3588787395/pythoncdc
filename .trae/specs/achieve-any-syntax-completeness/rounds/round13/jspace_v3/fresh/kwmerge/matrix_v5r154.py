# rr-v5r154 [v154-KWMERGE] 变体矩阵（A/B 双文件交换：HEAD 254d2751 vs v154 工作树）
# 功效案：kwargs 保序溅射族（**a 与具名关键字/多溅射混合——重建器 kwargs 序保持）
# 控制案：单溅射/纯具名/星号/字典显示 **update/前轮家族 回归防护
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r154matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    'E1_mixed': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'E2_multi_kw': """def g(d, kw):
    return d.call(**kw, x=1, y=2)
""",
    'E3_double_splat': """def h(d, a, b):
    return d.call(**a, **b)
""",
    'E4_splat_first_many': """def i(d, a, b):
    return d.call(**a, x=1, **b)
""",
    'E5_complex_kwval': """def j(d, a, x):
    return d.call(**a, deep=x + 1)
""",
    'C1_single_splat': """def f1(d, kw):
    return d.call(**kw)
""",
    'C2_named_only': """def f2(d):
    return d.call(x=1, y=2)
""",
    'C3_star_only': """def f3(d, xs):
    return d.call(*xs)
""",
    'C4_star_splat': """def f4(d, xs, kw):
    return d.call(*xs, **kw)
""",
    'C5_all_legacy': """def f5(d, xs, kw):
    return d.call(1, *xs, **kw)
""",
    'C6_dict_update': """def f6(a):
    r = {**a, 'k': 1}
    return r
""",
    'C7_mdiff3': """def gen(line_iterator):
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
    'C8_dual_unpack': """def f8(x, y):
    (a, b), (c, d) = x, y
    return a + b + c + d
""",
    'C9_latch_if': """def gen9(diffs):
    for fromdata, todata, flag in diffs:
        fromlist, tolist = [], []
        while fromlist or tolist:
            if fromlist:
                fromdata = fromlist.pop(0)
            else:
                fromdata = ('', ' ')
            yield (fromdata, todata, flag)
""",
    'C10_na5': """def f10(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
""",
    'C11_b116': """def f11(a, b):
    if a:
        if b:
            return None
    return None
""",
}

FILES = ('core/ast_nodes.py', 'core/cfg/ast_converter.py', 'core/cfg/code_generator.py')


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
    print('%-22s %-14s %s' % (name, status, bstat))
    if not same:
        print('  ---- A(HEAD) ----')
        for l in prod_a.splitlines():
            print('  ', l)
        print('  ---- B(v154) ----')
        for l in prod_b.splitlines():
            print('  ', l)
