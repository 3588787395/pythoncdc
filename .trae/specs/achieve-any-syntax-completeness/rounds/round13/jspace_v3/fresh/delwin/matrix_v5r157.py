# rr-v5r157 [v157-DELWIN] 变体矩阵（A/B 交换：HEAD 4b8d5a1e vs v157 工作树）
# 功效案：IfRegion 条件块前置语句段 DELETE_SUBSCR/DELETE_ATTR 操作数窗口形
# （urllib.request.urlcleanup 实形 del _url_tempfiles[:]）
# 控制案：简单名 del（v133 既有）/循环体 del（loop-exit 机）/非窗口残留形/前轮家族
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r157matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    # ---- 功效案（HEAD-TEXT-DIFF → v157 JUDGE-EQUAL）----
    'E1_urlcleanup': """_tmp = []
_opener = None

def cleanup():
    global _opener
    for t in _tmp:
        try:
            print(t)
        except OSError:
            pass
    del _tmp[:]
    if _opener:
        _opener = None
""",
    'E2_del_slice_min': """def f(seq, flag):
    del seq[:]
    if flag:
        print(flag)
    return seq
""",
    'E3_del_attr_win': """def f(obj, flag):
    del obj.attr
    if flag:
        print(flag)
""",
    'E4_del_key_const': """def f(d, flag, k):
    del d[k]
    if flag:
        print(flag)
""",
    'E5_del_multilevel': """def f(a, b, flag):
    del a[b][0]
    if flag:
        print(flag)
""",
    'E6_del_rslice': """def f(seq, flag):
    del seq[2:]
    if flag:
        print(flag)
""",
    'E7_del_multi_target': """def f(a, b, flag):
    del a[:], b[:]
    if flag:
        print(flag)
""",
    # ---- 控制案（SAME 预期）----
    'C1_plain_del': """def f(x, flag):
    del x
    if flag:
        print(flag)
    return 0
""",
    'C2_loop_body_del': """def f(d, items):
    for it in items:
        try:
            print(it)
        except OSError:
            pass
    del d[:]
    return d
""",
    'C3_del_no_if': """def f(seq):
    del seq[:]
    return seq
""",
    'C4_del_mid_window_extra': """def f(a, b, flag):
    t = a
    del b[:]
    if flag:
        print(flag)
    return t
""",
    'C5_kwmerge': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'C6_dual_unpack': """def f(x, y):
    (a, b), (c, d) = x, y
    return a + b + c + d
""",
    'C7_cfo2': """def f(src, dst, length=None, bufsize=None):
    bufsize = bufsize or 16 * 1024
    if length == 0:
        return
    print(bufsize, length)
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
        print('  ---- B(v157) ----')
        for l in prod_b.splitlines():
            print('  ', l)
