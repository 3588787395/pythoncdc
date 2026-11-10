# rr-v5r149 [v149-NOTELIF] 变体矩阵（A/B 单文件交换：HEAD 4d22f2fb vs v149 工作树）
# 功效案：否定链式条件校验 if（elif 吸收孤儿化 raise 族，get_close_matches 实形）
# 控制案：合法 elif 链/单块否定 elif/链式比较 elif/v148 族/B116 原形 回归防护
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r149matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    # 功效案 1：gcm 最小形（前置校验 if + 否定链式校验 if + raise）
    'E1_gcm_min': """def f(word, possibilities, n=3, cutoff=0.6):
    if not n > 0:
        raise ValueError('n must be > 0')
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError('cutoff must be in [0.0, 1.0]')
    result = []
    s = list(word)
    for x in possibilities:
        if len(x) > 2:
            result.append((x, s))
    return result
""",
    # 功效案 2：否定链式校验（无前置 if，独立成句）
    'E2_solo_chain': """def g(x):
    if not 0.0 <= x <= 1.0:
        raise ValueError('out of range')
    return x * 2
""",
    # 功效案 3：difflib 实形（f-string raise + 全函数）
    'E3_gcm_real': """def get_close_matches(word, possibilities, n=3, cutoff=0.6):
    if not n > 0:
        raise ValueError(f'n must be > 0: {n!r}')
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError(f'cutoff must be in [0.0, 1.0]: {cutoff!r}')
    result = []
    s = list(word)
    for x in possibilities:
        if len(x) > 2:
            result.append(x)
    return result[:n]
""",
    # 控制案 1：合法 elif 链 + else（正极性）
    'C1_elif_else': """def f(a, b):
    if a > 1:
        x = 1
    elif b > 2:
        x = 2
    else:
        x = 3
    return x
""",
    # 控制案 2：单块否定 elif（假边立即后继=链臂，B109 取反渲染）
    'C2_neg_elif': """def f(a, b):
    if a:
        y = 1
    elif not b:
        y = 2
    else:
        y = 3
    return y
""",
    # 控制案 3：单块否定 elif 终态臂（return）
    'C3_neg_elif_ret': """def f(a, b):
    if a:
        return 1
    elif not b:
        return 2
    return 3
""",
    # 控制案 4：链式比较 elif（0 < x < 10 形，cleanup 跳过机制保护对象）
    'C4_chain_elif': """def f(x):
    if x > 100:
        r = 'big'
    elif 0 < x < 10:
        r = 'small'
    else:
        r = 'mid'
    return r
""",
    # 控制案 5：v148 ggo 尾族（NOTTAIL 豁免维持）
    'C5_ggo_tail': """def g(codes, n=3):
    group = []
    for tag in codes:
        group.append(tag)
    if group and not (len(group) == 1 and group[0] == 'equal'):
        yield group
""",
    # 控制案 6：B116 原形（逐语句嵌套 and 链 None sink）
    'C6_b116_nested': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
    # 控制案 7：na5 while 嵌套链（v144 族）
    'C7_na5': """def f(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
""",
    # 控制案 8：守卫嵌套（G1 预存在）
    'C8_guard_nest': """def f(a, b, c, d):
    if a:
        while b and (c or d):
            b -= 1
    return b
""",
    # 控制案 9：否定链式校验 + 尾随 if（非 raise 体）
    'C9_chain_body': """def f(x):
    if not 0.0 <= x <= 1.0:
        x = 0.5
    if x > 0.5:
        return 1
    return 0
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
    print('%-18s %-14s %s' % (name, status, bstat))
    if not same:
        print('  ---- A(HEAD) ----')
        for l in prod_a.splitlines():
            print('  ', l)
        print('  ---- B(v149) ----')
        for l in prod_b.splitlines():
            print('  ', l)
