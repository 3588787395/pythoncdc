# rr-v5r160 [v160-DEEPRET] 变体矩阵（A/B 交换：HEAD 37a1f04c vs v160 工作树）
# 功效案：深层循环内 return 的 N 对帧清理前瞻（find_user_password 实形）
# 控制案：1/2 层既有形/无循环 return/前轮家族
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r160matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    # ---- 功效案（HEAD-TEXT-DIFF → v160 JUDGE-EQUAL）----
    'E1_find_user_pw': """class Mgr:
    def find(self, realm, authuri, cond):
        domains = self.passwd.get(realm, {})
        for default_port in (True, False):
            reduced = cond(authuri, default_port)
            for uris, authinfo in domains.items():
                for uri in uris:
                    if self.is_sub(uri, reduced):
                        return authinfo
        return None, None
""",
    'E2_deep3_min': """def f(domains, authuri, cond):
    for default_port in (True, False):
        reduced = cond(authuri, default_port)
        for uris, authinfo in domains.items():
            for uri in uris:
                if self_check(uri, reduced):
                    return authinfo
    return None, None
""",
    'E3_deep4': """def f(a, b, c, d, cond):
    for x in a:
        for y in b:
            for z in c:
                for w in d:
                    if cond(x, y, z, w):
                        return w
    return None
""",
    'E4_deep3_retuple': """def f(a, b, c, cond):
    for x in a:
        for y in b:
            for z in c:
                if cond(x, y, z):
                    return (x, y, z)
    return None
""",
    'E5_deep3_2ret': """def f(a, b, c, cond):
    for x in a:
        for y in b:
            for z in c:
                if cond(x, y, z):
                    return z
                if cond(y, x, z):
                    return x
    return None
""",
    # ---- 控制案（SAME 预期）----
    'C1_deep1': """def f(d, cond):
    for uri in d:
        if cond(uri):
            return uri
    return None
""",
    'C2_deep2': """def f(d, cond):
    for k, v in d.items():
        for uri in v:
            if cond(uri):
                return uri
    return None
""",
    'C3_no_loop_ret': """def f(x, cond):
    if cond(x):
        return x
    return None
""",
    'C4_loop_no_ret': """def f(a, b, cond):
    for x in a:
        for y in b:
            if cond(x, y):
                print(x, y)
    return None
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
    'C7_notcond': """def f(x, T, y, z):
    x = prep(x)
    if not (x in T and y or z == 'P'):
        raise ValueError(x, y, z)
    return x
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
        print('  ---- B(v160) ----')
        for l in prod_b.splitlines():
            print('  ', l)
