# rr-v5r163 变体矩阵（A 侧固定 f7d80873；B 侧 r163 工作树）（A/B 交换：HEAD f7d80873 vs v161 工作树）
# 功效案：融合 not or→and 混合链族（open_local_file 实形 + 变体）
# 控制案：既有 not-or/or-and/and-not/双not-or/not包裹/嵌套形/前轮家族
# 交换文件仅 core/cfg/region_analyzer.py（本轮修复单文件）；每案先 B 后 A 再恢复 WORK。
# 注：相对 r160 模板在循环外加 try/finally 恢复 WORK 并断言恢复成功（防中断停在 HEAD 版）。
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r163matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    # ---- 功效案（HEAD-TEXT-DIFF → v161 JUDGE-EQUAL；E161_olf_real/E161_not_or_and HEAD 已知 factored 反转）----
    'E161_olf_real': """def open_local_file(self, req):
    host = req.host
    localfile = url2pathname(req.selector)
    if not host or (not port and self.get_host(localfile) in self.get_names()):
        return localfile
    raise URLError('file not on local host')
""",
    'E161_not_or_and': """def f(a, b, c):
    if not a or (b and c):
        return 1
    return 0
""",
    'E161_not_or_notand': """def f(host, port, names):
    if not host or (not port and host in names):
        return 1
    return 0
""",
    'E161_pre_if': """def f(a, b, c, flag):
    if flag:
        print(flag)
    if not a or (b and c):
        return 1
    return 0
""",
    'E161_try_wrap': """def f(a, b, c):
    try:
        if not a or (b and c):
            return 1
    finally:
        cleanup()
    return 0
""",
    'E161_and3': """def f(a, b, c, d):
    if not a or (b and c and d):
        return 1
    return 0
""",
    # ---- 控制案（SAME + JUDGE-EQUAL 预期；C161_b116 预存在 JUDGE-DIFF）----
    'C161_not_or': """def f(a, b):
    if not a or b:
        return 1
    return 0
""",
    'C161_or_and': """def f(a, b, c):
    if a or (b and c):
        return 1
    return 0
""",
    'C161_and_not': """def f(a, b):
    if a and not b:
        return 1
    return 0
""",
    'C161_not_or_not': """def f(a, b):
    if not a or not b:
        return 1
    return 0
""",
    'C161_not_and_or': """def f(a, b, c):
    if not (a and b or c):
        return 1
    return 0
""",
    'C161_nested_ifelse': """def f(a, b, c):
    if a:
        if b:
            return 1
    else:
        return 2
    return 0
""",
    'C161_plain_and': """def f(a, b, c):
    if a and b and c:
        return 1
    return 0
""",
    'C161_notcond': """def f(x, T, y, z):
    x = prep(x)
    if not (x in T and y or z == 'P'):
        raise ValueError(x, y, z)
    return x
""",
    'C161_kwmerge': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'C161_delwin': """def f(seq, flag):
    del seq[:]
    if flag:
        print(flag)
    return seq
""",
    'C161_binparen': """def f(a, b):
    return a * (b * 2)
""",
    'C161_retfin': """def f(self, g, x):
    try:
        if x:
            return g(x)
        return None
    finally:
        self.done = True
""",
    'C161_b116': """def f(a, b):
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


BASE_COMMIT = "f7d80873"  # rr-v5r160 提交：本轮 A 侧基线固定提交，不随 HEAD 推进漂移


def git_show_head(f):
    r = subprocess.run(['git', '-C', REPO, 'show', '%s:%s' % (BASE_COMMIT, f)],
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
assert b'v161-NOTMIX' in WORK[FILES[0]], 'work tree analyzer missing v161-NOTMIX marker'
assert b'v161-NOTMIX' not in HEAD[FILES[0]], 'base commit already contains v161 patch?'

print('==== SUMMARY ====')
try:
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
            print('  ---- A(base %s) ----' % BASE_COMMIT)
            for l in prod_a.splitlines():
                print('  ', l)
            print('  ---- B(v161) ----')
            for l in prod_b.splitlines():
                print('  ', l)
finally:
    write_files(WORK)
    for f in FILES:
        assert open(os.path.join(REPO, f), 'rb').read() == WORK[f], 'restore failed: %s' % f
    print('==== FILES RESTORED (v161 work tree) ====')
