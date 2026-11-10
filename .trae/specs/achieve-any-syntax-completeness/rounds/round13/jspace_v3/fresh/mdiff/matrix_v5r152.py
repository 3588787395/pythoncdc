# rr-v5r152 [v152-HANDLERRET/v152-ORCLAIM/v152-LATCH/v152-DUALUNPACK2] 变体矩阵
# A/B 单文件交换：HEAD dda01bb9 vs v152 工作树
import os, subprocess, py_compile, sys, types, typing

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r152matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    # 功效案 1：mdiff3 形（共享头 while-True + or 条件 + except return）——HANDLERRET+ORCLAIM
    'E1_mdiff3': """def gen(line_iterator):
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
    # 功效案 2：_line_wrapper 形（while or 条件 + 体内同变量 if/else）——LATCH
    'E2_latch_if': """def gen(diffs):
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
    # 功效案 3：while 前缀链式解包——DUALUNPACK2
    'E3_dual_unpack': """def f(pairs):
    total = 0
    while total < len(pairs):
        (a, b), (c, d) = pairs[total], pairs[total + 1]
        total += a + b + c + d
    return total
""",
    # 控制案 1：独立连续解包（各自值缓冲——不合并）
    'C1_indep_unpacks': """def f(xs, ys):
    a, b = xs
    c, d = ys
    return a + b + c + d
""",
    # 控制案 2：单解包
    'C2_single_unpack': """def f(xs):
    a, b = xs
    return a + b
""",
    # 控制案 3：v150 fancy 尾（RAISETERM 族维持）
    'C3_fancy_tail': """def _fancy_helper(a, alo, ahi, b, blo, bhi):
    yield ('h',)


def _qformat(aline, bline, atags, btags):
    yield ('q', aline)


class Seq:
    def set_seqs(self, x, y):
        pass

    def get_opcodes(self):
        return [('replace', 0, 1, 0, 1), ('equal', 1, 2, 1, 2)]


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
    # 控制案 4：na5 while 嵌套链
    'C4_na5': """def f(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
""",
    # 控制案 5：v149 gcm 校验对
    'C5_gcm_min': """def f(word, possibilities, n=3, cutoff=0.6):
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
    # 控制案 6：B116 原形
    'C6_b116_nested': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
    # 控制案 7：v151 outer yield（OUTERYIELD 族维持）
    'C7_outer_yield': """def gen(line_iterator):
    fromlines, tolines = ([], [])
    while True:
        while len(fromlines) == 0:
            from_line, to_line, found_diff = next(line_iterator)
            if from_line is not None:
                fromlines.append((from_line, found_diff))
            if to_line is not None:
                tolines.append((to_line, found_diff))
        from_line, fromdiff = fromlines.pop(0)
        to_line, todiff = tolines.pop(0)
        yield (from_line, to_line, fromdiff | todiff)
""",
    # 控制案 8：简单 handler return（无循环——HANDLERRET 豁免不触发）
    'C8_plain_handler': """def f(it):
    try:
        return next(it)
    except StopIteration:
        return None
""",
    # 控制案 9：handler break（B140 域维持）
    'C9_handler_break': """def f(it):
    while True:
        try:
            x = next(it)
        except StopIteration:
            break
        yield x
""",
    # 控制案 10：真 while-test 共享头（无 yield）
    'C10_shared_notest': """def f(items):
    i = 0
    while i < len(items):
        j = 0
        while j < 3:
            j += 1
        i += 1
    return i
""",
    # 控制案 11：async await（轮询域排除）
    'C11_async': """async def f(x):
    await x
    return 1
""",
    # 控制案 12：and 链 while（v143 域）
    'C12_and_chain': """def f(items):
    i = 0
    while i < len(items) and items[i] != 'end':
        i += 1
    return i
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
    print('%-22s %-14s %s' % (name, status, bstat))
    if not same:
        print('  ---- A(HEAD) ----')
        for l in prod_a.splitlines():
            print('  ', l)
        print('  ---- B(v152) ----')
        for l in prod_b.splitlines():
            print('  ', l)
