# rr-v5r150 [v150-RAISETERM] 变体矩阵（A/B 单文件交换：HEAD 5d7a004b vs v150 工作树）
# 功效案：生成器 if/else 内层 raise 链（RAISETERM 误清空族，_fancy_replace 实形）
# 控制案：真 raise 臂/合法 elif/前轮族 回归防护
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r150matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    # 功效案 1：fr2 复现（then 臂含 for+if/elif/else+raise 链 + 尾 yield-from）
    'E1_fr2': open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fr2_src.py'), encoding='utf-8').read(),
    # 功效案 2：真 _fancy_replace 尾形（独立函数）
    'E2_fancy_tail': """def _fancy_helper(a, alo, ahi, b, blo, bhi):
    yield ('h',)


def _qformat(aline, bline, atags, btags):
    yield ('q', aline)


class Seq:
    def set_seqs(self, x, y):
        pass

    def get_opcodes(self):
        return [('replace', 0, 1, 0, 1), ('equal', 1, 2, 1, 2), ('delete', 2, 3, 1, 1)]


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
            elif tag == 'delete':
                atags += '-' * la
            elif tag == 'insert':
                btags += '+' * lb
            elif tag == 'equal':
                atags += ' ' * la
                btags += ' ' * lb
            else:
                raise ValueError('unknown tag')
        yield from _qformat(aelt, belt, atags, btags)
    else:
        yield '  ' + aelt
    yield from _fancy_helper(a, best_i + 1, 9, b, best_j + 1, 9)
""",
    # 控制案 1：真 raise 臂 + else（规则原形——raise 即臂终点，须维持清空行为）
    'C1_true_raise': """def f(c, x):
    if c:
        raise ValueError('bad')
    else:
        x = x + 1
    return x
""",
    # 控制案 2：then 臂内嵌 if 逃逸 + 尾 raise（臂闭合形——JF 目标在臂内）
    'C2_nested_raise': """def f(c, d, x):
    if c:
        if d:
            x = 1
        else:
            x = 2
        raise ValueError('bad')
    else:
        x = 3
    return x
""",
    # 控制案 3：v148 ggo 尾族
    'C3_ggo_tail': """def g(codes, n=3):
    group = []
    for tag in codes:
        group.append(tag)
    if group and not (len(group) == 1 and group[0] == 'equal'):
        yield group
""",
    # 控制案 4：v149 gcm 校验对
    'C4_gcm_min': """def f(word, possibilities, n=3, cutoff=0.6):
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
    # 控制案 5：单块否定 elif（v149 保护对象）
    'C5_neg_elif': """def f(a, b):
    if a:
        y = 1
    elif not b:
        y = 2
    else:
        y = 3
    return y
""",
    # 控制案 6：B116 原形
    'C6_b116_nested': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
    # 控制案 7：na5 while 嵌套链
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
        print('  ---- B(v150) ----')
        for l in prod_b.splitlines():
            print('  ', l)
