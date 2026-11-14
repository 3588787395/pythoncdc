# rr-v5r161 [v161-NOTMIX] A/B 回归电池（458 案；五文件交换）
#   以 r160_regress.py 为模板：R110 169 案 + V111..V122/V148..V160 累计案 + V161 矩阵 19 案。
#   逐案 compile -> pyc -> decompile CURRENT(v161) 与 HEAD(f7d80873) 版
#   （git-show 五文件交换：analyzer/generator/ast_nodes/ast_converter/code_generator）
#   -> 比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r161regress/（独立 TMP，干净重跑）。
import os, sys, re, glob, json, types, py_compile, subprocess
from collections import defaultdict

REPO = 'F:/Downloads/pythoncdc-main'
BASE = REPO + '/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh'
EV = BASE + '/mixcond'
RAG = REPO + '/core/cfg/region_analyzer.py'
RAG2 = REPO + '/core/cfg/region_ast_generator.py'
# [v154-KWMERGE] 本轮改动三文件并入交换集（五文件 A/B）
AN = REPO + '/core/ast_nodes.py'
AC = REPO + '/core/cfg/ast_converter.py'
CG = REPO + '/core/cfg/code_generator.py'
V148_FILES = (RAG, RAG2, AN, AC, CG)
PY = 'D:/Python/python.exe'
GIT = 'E:/Program Files/PortableGit/bin/git.exe'
HEAD = 'f7d80873'
R110 = BASE + '/chainfor_foriter/r110_regress_result.txt'
MP = BASE + '/orandchain_if/matrix_products'
TMP = 'D:/temp/opencode/cl_layout/r163regress'
OUTDIR = TMP + '/v163'
OUTDIR_H = TMP + '/head'
CASEDIR = TMP + '/cases'

sys.path.insert(0, BASE + '/orchain_armbody')
sys.path.insert(0, BASE + '/tailscope_emit')
sys.path.insert(0, EV)
sys.path.insert(0, BASE + '/whileyield_break')
sys.path.insert(0, BASE + '/notboolop_orand')
sys.path.insert(0, BASE + '/bareret_w19')
sys.path.insert(0, BASE + '/foldret_arm')
sys.path.insert(0, BASE + '/eliftest_loop')
sys.path.insert(0, BASE + '/andnot_yieldarm')
sys.path.insert(0, BASE + '/trytop_loop')
sys.path.insert(0, BASE + '/armfall_ifmerge')
from matrix_v5r118 import CASES as V118_CASES
from matrix_v5r119 import CASES as V119_CASES
from matrix_v5r120 import CASES as V120_CASES
from matrix_v5r122 import CASES as V122_CASES

# [v148-NOTTAIL] 本轮矩阵 13 案（功效 E1-E3 + 控制 C1-C10）
V148_CASES = {
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

# [v149-NOTELIF] 本轮矩阵追加案（功效 E149 + 关键控制 C149）
V149_CASES = {
    'E149_gcm_min': """def f(word, possibilities, n=3, cutoff=0.6):
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
    'E149_gcm_real': """def get_close_matches(word, possibilities, n=3, cutoff=0.6):
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
    'C149_elif_else': """def f(a, b):
    if a > 1:
        x = 1
    elif b > 2:
        x = 2
    else:
        x = 3
    return x
""",
    'C149_neg_elif': """def f(a, b):
    if a:
        y = 1
    elif not b:
        y = 2
    else:
        y = 3
    return y
""",
    'C149_neg_elif_ret': """def f(a, b):
    if a:
        return 1
    elif not b:
        return 2
    return 3
""",
    'C149_chain_elif': """def f(x):
    if x > 100:
        r = 'big'
    elif 0 < x < 10:
        r = 'small'
    else:
        r = 'mid'
    return r
""",
}

# [v150-RAISETERM] 本轮矩阵追加案（功效 + 关键控制）
V150_CASES = {
    'E150_fr2': """def _fancy_helper(a, alo, ahi, b, blo, bhi):
    yield ('h',)


def _qformat(aline, bline, atags, btags):
    yield ('q', aline)


class Seq:
    def set_seqs(self, x, y):
        pass

    def get_opcodes(self):
        return [('replace', 0, 1, 0, 1), ('equal', 1, 2, 1, 2)]


def fancy_tail(a, alo, ahi, b, blo, bhi, best_ratio, cutoff, cruncher):
    eqi = eqj = None
    if best_ratio < cutoff:
        if eqi is None:
            yield from _fancy_helper(a, alo, ahi, b, blo, bhi)
            return None
        best_i, best_j, best_ratio = eqi, eqj, 1.0
    else:
        eqi = None
    yield from _fancy_helper(a, alo, best_i, b, blo, best_j)
    aelt, belt = a[best_i], b[best_j]
    if eqi is None:
        atags = btags = ''
        cruncher.set_seqs(aelt, belt)
        for tag, ai1, ai2, bj1, bj2 in cruncher.get_opcodes():
            la, lb = ai2 - ai1, bj2 - bj1
            if tag == 'replace':
                atags += '^' * la
                btags += '^' * lb
                continue
            elif tag == 'delete':
                atags += '-' * la
                continue
            elif tag == 'insert':
                btags += '+' * lb
                continue
            elif tag == 'equal':
                atags += ' ' * la
                btags += ' ' * lb
                continue
            else:
                raise ValueError('unknown tag')
        yield from _qformat(aelt, belt, atags, btags)
    else:
        yield '  ' + aelt
    yield from _fancy_helper(a, best_i + 1, ahi, b, best_j + 1, bhi)
""",
    'E150_fancy_tail': """def _fancy_helper(a, alo, ahi, b, blo, bhi):
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
    'C150_true_raise': """def f(c, x):
    if c:
        raise ValueError('bad')
    else:
        x = x + 1
    return x
""",
    'C150_nested_raise': """def f(c, d, x):
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
}

# 既有登记差案（逐字节同签名重点核验）
REGISTERED = ['w28_shapes', 'na5', 'pe8', 'pe8_target', 'nb2',
              'ca6', 'ca13', 'ca15', 'cb5', 'pd8_prod']


# [v151-OUTERYIELD] 本轮矩阵 10 案（功效 E1-E2 + 控制 C1-C8）
V151_CASES = {
    'E151_outer_yield': """def gen(line_iterator):
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
    'E151_nested': """def outer(it):
    diff = iter(it)

    def inner():
        acc = []
        while True:
            while len(acc) == 0:
                x = next(diff, None)
                if x is not None:
                    acc.append(x)
            yield acc.pop(0)

    yield from inner()
""",
    'C151_whiletrue_break': """def f(n):
    while True:
        n -= 1
        if n <= 0:
            break
    return n
""",
    'C151_shared_notest': """def f(items):
    i = 0
    while i < len(items):
        j = 0
        while j < 3:
            j += 1
        i += 1
    return i
""",
    'C151_async': """async def f(x):
    await x
    return 1
""",
    'C151_yield_whiletrue': """def f():
    while True:
        yield 1
""",
    'C151_fancy_tail': """def _fancy_helper(a, alo, ahi, b, blo, bhi):
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
    'C151_na5': """def f(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
""",
    'C151_gcm_min': """def f(word, possibilities, n=3, cutoff=0.6):
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
    'C151_b116_nested': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
}



# [v152-HANDLERRET/ORCLAIM/LATCH/DUALUNPACK2] 本轮矩阵 15 案（功效 E1-E2 + 登记 E3 + 控制 C1-C12）
V152_CASES = {
    'E152_mdiff3': """def gen(line_iterator):
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
    'E152_latch_if': """def gen(diffs):
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
    'E152_dual_unpack': """def f(pairs):
    total = 0
    while total < len(pairs):
        (a, b), (c, d) = pairs[total], pairs[total + 1]
        total += a + b + c + d
    return total
""",
    'C152_indep_unpacks': """def f(xs, ys):
    a, b = xs
    c, d = ys
    return a + b + c + d
""",
    'C152_single_unpack': """def f(xs):
    a, b = xs
    return a + b
""",
    'C152_fancy_tail': """def _fancy_helper(a, alo, ahi, b, blo, bhi):
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
    'C152_na5': """def f(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
""",
    'C152_gcm_min': """def f(word, possibilities, n=3, cutoff=0.6):
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
    'C152_b116_nested': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
    'C152_outer_yield': """def gen(line_iterator):
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
    'C152_plain_handler': """def f(it):
    try:
        return next(it)
    except StopIteration:
        return None
""",
    'C152_handler_break': """def f(it):
    while True:
        try:
            x = next(it)
        except StopIteration:
            break
        yield x
""",
    'C152_shared_notest': """def f(items):
    i = 0
    while i < len(items):
        j = 0
        while j < 3:
            j += 1
        i += 1
    return i
""",
    'C152_async': """async def f(x):
    await x
    return 1
""",
    'C152_and_chain': """def f(items):
    i = 0
    while i < len(items) and items[i] != 'end':
        i += 1
    return i
""",
}



# [v153-RESIDUNPACK] 本轮矩阵 19 案（功效 E1-E6 六位形 + 控制 C1-C13）
V153_CASES = {
    'E153_toplevel': """def f1(x, y):
    (a, b), (c, d) = x, y
    return a + b + c + d
""",
    'E153_whilebody': """def f2(pairs):
    total = 0
    while total < len(pairs):
        (a, b), (c, d) = pairs[total], pairs[total + 1]
        total += a + b + c + d
    return total
""",
    'E153_forbody': """def f3(pairs):
    out = []
    for p in pairs:
        (a, b), (c, d) = p, p
        out.append(a + b + c + d)
    return out
""",
    'E153_ifbody': """def f4(x, y):
    if x:
        (a, b), (c, d) = x, y
    return (a, b, c, d)
""",
    'E153_ifelse_seq': """def f5(x, y):
    if x:
        t = 1
    else:
        t = 2
    (a, b), (c, d) = x, y
    return a + b + c + d + t
""",
    'E153_after_while': """def f6(xs):
    i = 0
    while i < len(xs):
        i += 1
    (a, b), (c, d) = xs[0], xs[1]
    return a + b + c + d
""",
    'C153_indep': """def f(xs, ys):
    a, b = xs
    c, d = ys
    return a + b + c + d
""",
    'C153_single': """def f(xs):
    a, b = xs
    return a + b
""",
    'C153_nested': """def f(x):
    a, (b, c) = x
    return a + b + c
""",
    'C153_starred': """def f(xs):
    a, *b = xs
    return (a, b)
""",
    'C153_walrus': """def f(g):
    a, b = (d := g())
    return a + b + d
""",
    'C153_attr_target': """class R:
    def __init__(self, f):
        self.conn, self.cur = f()
""",
    'C153_subscr_target': """def f(d, g):
    d['x'], d['y'] = g()
    return d
""",
    'C153_mdiff3': """def gen(line_iterator):
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
    'C153_latch_if': """def gen(diffs):
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
    'C153_line_wrapper_real': """class HtmlDiff:
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
    'C153_fancy_tail': """def _fancy_helper(a, alo, ahi, b, blo, bhi):
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
    'C153_na5': """def f(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
""",
    'C153_b116': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
}



# [v154-KWMERGE] 本轮矩阵 16 案（功效 E1-E5 + 控制 C1-C11）
V154_CASES = {
    'E154_mixed': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'E154_multi_kw': """def g(d, kw):
    return d.call(**kw, x=1, y=2)
""",
    'E154_double_splat': """def h(d, a, b):
    return d.call(**a, **b)
""",
    'E154_splat_first_many': """def i(d, a, b):
    return d.call(**a, x=1, **b)
""",
    'E154_complex_kwval': """def j(d, a, x):
    return d.call(**a, deep=x + 1)
""",
    'C154_single_splat': """def f1(d, kw):
    return d.call(**kw)
""",
    'C154_named_only': """def f2(d):
    return d.call(x=1, y=2)
""",
    'C154_star_only': """def f3(d, xs):
    return d.call(*xs)
""",
    'C154_star_splat': """def f4(d, xs, kw):
    return d.call(*xs, **kw)
""",
    'C154_all_legacy': """def f5(d, xs, kw):
    return d.call(1, *xs, **kw)
""",
    'C154_dict_update': """def f6(a):
    r = {**a, 'k': 1}
    return r
""",
    'C154_mdiff3': """def gen(line_iterator):
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
    'C154_dual_unpack': """def f8(x, y):
    (a, b), (c, d) = x, y
    return a + b + c + d
""",
    'C154_latch_if': """def gen9(diffs):
    for fromdata, todata, flag in diffs:
        fromlist, tolist = [], []
        while fromlist or tolist:
            if fromlist:
                fromdata = fromlist.pop(0)
            else:
                fromdata = ('', ' ')
            yield (fromdata, todata, flag)
""",
    'C154_na5': """def f10(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
""",
    'C154_b116': """def f11(a, b):
    if a:
        if b:
            return None
    return None
""",
}



# [v155-CONDLEAK] 本轮矩阵 11 案（功效 E1-E2 + 控制域 E3-E5 + 回归 C1-C6）
V155_CASES = {
    'E155_cfo2': """def f(src, dst, length=None, bufsize=None):
    bufsize = bufsize or 16 * 1024
    if length == 0:
        return
    if length is None:
        print(src, dst, bufsize)
        return
    blocks, remainder = divmod(length, bufsize)
    for b in range(blocks):
        print(b)
    if remainder != 0:
        print(remainder)
""",
    'E155_minimal': """def f2(src, dst, length=None, bufsize=None):
    bufsize = bufsize or 16 * 1024
    if length == 0:
        return
    print(bufsize, length)
""",
    'E155_guard_clause': """def f3(a, b, z):
    x = a or b
    y = len(z)
    if not z:
        raise ValueError('empty')
    return x, y
""",
    'E155_precall': """def f4(a, b, g):
    x = a or b
    if g(x) and b:
        return 1
    return 0
""",
    'E155_cond_context': """def f5(a, b):
    if a > 0 and b:
        return 1
    return 0
""",
    'C155_kwmerge': """def f6(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'C155_dual_unpack': """def f7(x, y):
    (a, b), (c, d) = x, y
    return a + b + c + d
""",
    'C155_mdiff3': """def gen(line_iterator):
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
    'C155_latch_if': """def gen9(diffs):
    for fromdata, todata, flag in diffs:
        fromlist, tolist = [], []
        while fromlist or tolist:
            if fromlist:
                fromdata = fromlist.pop(0)
            else:
                fromdata = ('', ' ')
            yield (fromdata, todata, flag)
""",
    'C155_na5': """def f10(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
""",
    'C155_b116': """def f11(a, b):
    if a:
        if b:
            return None
    return None
""",
}



# [v156-BINPAREN] 本轮矩阵 17 案（功效 E1-E7 + 集内豁免控制 E8 + 既有域 C1-C9）
V156_CASES = {
    'E156_close': """def f(fileobj, NUL, BLOCKSIZE):
    fileobj.write(NUL * (BLOCKSIZE * 2))
    fileobj.write(NUL * (BLOCKSIZE * 3))
""",
    'E156_mul_minimal': """def f(a, b):
    return a * (b * 2)
""",
    'E156_add': """def f(a, b, c):
    return a + (b + c)
""",
    'E156_cross_mul_div': """def f(a, b, c):
    return a * (b / c)
""",
    'E156_cross_add_sub': """def f(a, b, c):
    return a + (b - c)
""",
    'E156_shift': """def f(a, b, c):
    return a << (b << c)
""",
    'E156_bitwise': """def f(a, b, c):
    return a | (b | c)
""",
    'E156_in_call_arg': """def f(a, b, c):
    return g(a % (b % c), a - (b % c))
""",
    'C156_left_nested': """def f(a, b, c):
    return a * b * c
""",
    'C156_div_legacy': """def f(a, b, c):
    return a - (b - c)
""",
    'C156_power_right': """def f(a, b, c):
    return a ** (b ** c)
""",
    'C156_lower_prec_right': """def f(a, b, c):
    return a * (b + c)
""",
    'C156_paren_left': """def f(a, b, c):
    return (a + b) * c
""",
    'C156_kwmerge': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'C156_dual_unpack': """def f(x, y):
    (a, b), (c, d) = x, y
    return a + b + c + d
""",
    'C156_cfo2': """def f(src, dst, length=None, bufsize=None):
    bufsize = bufsize or 16 * 1024
    if length == 0:
        return
    print(bufsize, length)
""",
    'C156_b116': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
}



# [v157-DELWIN] 本轮矩阵 17 案（功效 E1-E7+C4 窗口形 + 控制域 C1-C3/C5-C9）
V157_CASES = {
    'E157_urlcleanup': """_tmp = []
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
    'E157_del_slice_min': """def f(seq, flag):
    del seq[:]
    if flag:
        print(flag)
    return seq
""",
    'E157_del_attr_win': """def f(obj, flag):
    del obj.attr
    if flag:
        print(flag)
""",
    'E157_del_key_const': """def f(d, flag, k):
    del d[k]
    if flag:
        print(flag)
""",
    'E157_del_multilevel': """def f(a, b, flag):
    del a[b][0]
    if flag:
        print(flag)
""",
    'E157_del_rslice': """def f(seq, flag):
    del seq[2:]
    if flag:
        print(flag)
""",
    'E157_del_multi_target': """def f(a, b, flag):
    del a[:], b[:]
    if flag:
        print(flag)
""",
    'E157_del_after_assign': """def f(a, b, flag):
    t = a
    del b[:]
    if flag:
        print(flag)
    return t
""",
    'C157_plain_del': """def f(x, flag):
    del x
    if flag:
        print(flag)
    return 0
""",
    'C157_loop_body_del': """def f(d, items):
    for it in items:
        try:
            print(it)
        except OSError:
            pass
    del d[:]
    return d
""",
    'C157_del_no_if': """def f(seq):
    del seq[:]
    return seq
""",
    'C157_kwmerge': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'C157_dual_unpack': """def f(x, y):
    (a, b), (c, d) = x, y
    return a + b + c + d
""",
    'C157_cfo2': """def f(src, dst, length=None, bufsize=None):
    bufsize = bufsize or 16 * 1024
    if length == 0:
        return
    print(bufsize, length)
""",
    'C157_binparen': """def f(a, b):
    return a * (b * 2)
""",
    'C157_b116': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
}



# [v158-RETFIN] 本轮矩阵 16 案（功效 E1 + 同形控制 E2-E7 + 既有域 C1-C9）
V158_CASES = {
    'E158_http302': """def fetch(self, meth, url, headers):
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
    'E158_min_call': """def f(self, g, x):
    try:
        if x:
            return g(x)
        return None
    finally:
        self.done = True
""",
    'E158_arith': """def f(self, a, b):
    try:
        if a > b:
            return a + b * 2
        return 0
    finally:
        self.n += 1
""",
    'E158_nested_call': """def f(self, g, h, x):
    try:
        if g(x):
            return h(g(x))
        return None
    finally:
        self.n = 0
""",
    'E158_attr': """def f(self, x):
    try:
        if x:
            return self.handler(x)
        return None
    finally:
        self.flag = False
""",
    'E158_two_stmt_finally': """def f(self, g, x):
    try:
        if x:
            return g(x)
        return None
    finally:
        self.n = 0
        self.done = True
""",
    'E158_else_arm': """def f(self, g, x):
    try:
        if x:
            self.mark(x)
        else:
            return g(x)
        return None
    finally:
        self.n = 0
""",
    'C158_toplevel_return': """def f(self, g, x):
    try:
        return g(x)
    finally:
        self.n = 0
""",
    'C158_name_result': """def f(self, g, x):
    try:
        result = g(x)
        return result
    finally:
        self.n = 0
""",
    'C158_no_finally': """def f(g, x):
    if x:
        return g(x)
    return None
""",
    'C158_const_return': """def f(self, x):
    try:
        if x:
            return 0
        return 1
    finally:
        self.n = 0
""",
    'C158_handler_ret': """def f(it):
    while True:
        try:
            v = next(it)
        except StopIteration:
            return
        print(v)
""",
    'C158_kwmerge': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'C158_delwin': """def f(seq, flag):
    del seq[:]
    if flag:
        print(flag)
    return seq
""",
    'C158_binparen': """def f(a, b):
    return a * (b * 2)
""",
    'C158_b116': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
}



# [v159-NOTCOND] 本轮矩阵 15 案（功效 E1/E3-E6 + 零触碰控制 E2/C1-C9）
V159_CASES = {
    'E159_rr': """class Handler:
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        m = req.get_method()
        if (not (code in (301, 302, 303, 307, 308) and m in ('GET', 'HEAD')
                 or code in (301, 302, 303) and m == 'POST')):
            raise ValueError(req.full_url, code, msg, headers, fp)
        newurl = newurl.replace(' ', '%20')
        return newurl
""",
    'E159_preassign_and': """def f(x, T, y):
    x = prep(x)
    if x in T and y:
        print(x, y)
    return x
""",
    'E159_not_mixed': """def f(x, T, y, z):
    x = prep(x)
    if not (x in T and y or z == 'P'):
        raise ValueError(x, y, z)
    return x
""",
    'E159_not_single': """def f(x, T, y):
    x = prep(x)
    if not (x in T and y):
        raise ValueError(x, y)
    return x
""",
    'E159_two_preassign': """def f(a, T, b):
    a = prep(a)
    b = prep2(b)
    if not (a in T and b or a == 2):
        raise ValueError(a, b)
    return a, b
""",
    'E159_precall_shape': """def f(code, m, req, fp, newurl):
    m = req.get_method()
    if (not (code in (301, 302, 303, 307, 308) and m in ('GET', 'HEAD')
             or code in (301, 302, 303) and m == 'POST')):
        raise ValueError(req.full_url, code, m)
    return newurl
""",
    'C159_no_preassign': """def f(code, m):
    if (not (code in (301, 302, 303, 307, 308) and m in ('GET', 'HEAD')
             or code in (301, 302, 303) and m == 'POST')):
        raise ValueError(code, m)
    return code
""",
    'C159_true_mode': """def f(x, T, y):
    x = prep(x)
    if x in T or y:
        print(x, y)
    return x
""",
    'C159_compare': """def f(x, y, z):
    x = prep(x)
    if x == (y or z):
        print(x)
    return x
""",
    'C159_simple_var': """def f(x, y):
    x = prep(x)
    if x and y:
        print(x, y)
    return x
""",
    'C159_kwmerge': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'C159_delwin': """def f(seq, flag):
    del seq[:]
    if flag:
        print(flag)
    return seq
""",
    'C159_retfin': """def f(self, g, x):
    try:
        if x:
            return g(x)
        return None
    finally:
        self.done = True
""",
    'C159_binparen': """def f(a, b):
    return a * (b * 2)
""",
    'C159_b116': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
}



# [v160-DEEPRET] 本轮矩阵 14 案（功效 E1-E5 + 既有形控制 C1-C9）
V160_CASES = {
    'E160_find_user_pw': """class Mgr:
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
    'E160_deep3_min': """def f(domains, authuri, cond):
    for default_port in (True, False):
        reduced = cond(authuri, default_port)
        for uris, authinfo in domains.items():
            for uri in uris:
                if self_check(uri, reduced):
                    return authinfo
    return None, None
""",
    'E160_deep4': """def f(a, b, c, d, cond):
    for x in a:
        for y in b:
            for z in c:
                for w in d:
                    if cond(x, y, z, w):
                        return w
    return None
""",
    'E160_deep3_retuple': """def f(a, b, c, cond):
    for x in a:
        for y in b:
            for z in c:
                if cond(x, y, z):
                    return (x, y, z)
    return None
""",
    'E160_deep3_2ret': """def f(a, b, c, cond):
    for x in a:
        for y in b:
            for z in c:
                if cond(x, y, z):
                    return z
                if cond(y, x, z):
                    return x
    return None
""",
    'C160_deep1': """def f(d, cond):
    for uri in d:
        if cond(uri):
            return uri
    return None
""",
    'C160_deep2': """def f(d, cond):
    for k, v in d.items():
        for uri in v:
            if cond(uri):
                return uri
    return None
""",
    'C160_no_loop_ret': """def f(x, cond):
    if cond(x):
        return x
    return None
""",
    'C160_loop_no_ret': """def f(a, b, cond):
    for x in a:
        for y in b:
            if cond(x, y):
                print(x, y)
    return None
""",
    'C160_kwmerge': """def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
""",
    'C160_delwin': """def f(seq, flag):
    del seq[:]
    if flag:
        print(flag)
    return seq
""",
    'C160_notcond': """def f(x, T, y, z):
    x = prep(x)
    if not (x in T and y or z == 'P'):
        raise ValueError(x, y, z)
    return x
""",
    'C160_binparen': """def f(a, b):
    return a * (b * 2)
""",
    'C160_b116': """def f(a, b):
    if a:
        if b:
            return None
    return None
""",
}


# [v161-NOTMIX] 本轮矩阵 19 案（功效 E161 六案 + 控制 C161 十三案；与 matrix_v5r161.py 同名同源）
V161_CASES = {
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


EXCL = re.compile(
    r'(out|prod|regress|recompiled|_v[0-9]|sd_|matrix|probe|good|disc|'
    r'fielddiff|err|result|dis[0-9]|dump|hook|tree|ast|verify|baseline|'
    r'unclaimed|fix_|patch|decompiled)', re.I)


def norm(c):
    return (c.co_code.hex(), c.co_exceptiontable.hex(),
            c.co_names, c.co_varnames, c.co_freevars, c.co_cellvars,
            tuple(norm(k) if isinstance(k, types.CodeType) else k for k in c.co_consts))


def toplevels(c):
    return {k.co_name: norm(k) for k in c.co_consts if isinstance(k, types.CodeType)}


def fn_status(src_text, prod_text):
    try:
        s = toplevels(compile(src_text, 's', 'exec'))
        p = toplevels(compile(prod_text, 'p', 'exec'))
    except SyntaxError as se:
        return 'SYNTAX-ERR ' + se.msg[:40]
    rem = sorted(set(s) - set(p)); add = sorted(set(p) - set(s))
    chg = sorted(n for n in set(s) & set(p) if s[n] != p[n])
    if not rem and not add and not chg:
        return 'BYTE-EQUAL'
    return 'DIFF rem=%s add=%s chg=%s' % (rem, add, chg)


def build_cases():
    r110_names = [l.split()[0] for l in open(R110, encoding='utf-8')
                  if l.strip() and not l.startswith('TEXT-DIFF') and 'count' not in l]
    bn = defaultdict(list)
    for p in glob.glob(BASE + '/**/*.py', recursive=True):
        q = p.replace('\\', '/')
        if '/orandchain_if/' in q or '/notboolop_orand/' in q \
                or '/whileyield_break/' in q or '/argor_mergenop/' in q \
                or '/eliftest_loop/' in q or '/foldret_arm/' in q \
                or '/andnot_yieldarm/' in q or '/trytop_loop/' in q \
                or '/armfall_ifmerge/' in q or '/orchain_armbody/' in q or '/tailscope_emit/' in q or '/tupkey_subscript/' in q \
                or '/nbe_update/' in q or '/trivnop/' in q or '/excassert/' in q or '/swapassign/' in q or '/chainelse/' in q or '/modstmt/' in q or '/loopb234/' in q or '/chainunpack/' in q or '/loopb234b/' in q or '/selfloopb234/' in q or '/ftunpack/' in q or '/slbodyexpr/' in q or '/chainwalrus/' in q or '/slb234/' in q or '/boolopchain4/' in q or '/orchain/' in q or '/ornest2/' in q or '/orflat/' in q or '/orandtail/' in q or '/ornest/' in q or '/notail/' in q or '/outeryield/' in q or '/mdiff/' in q or '/residunpack/' in q or '/kwmerge/' in q or '/condleak/' in q or '/binparen/' in q or '/delwin/' in q or '/retfin/' in q or '/notcond/' in q or '/deepret/' in q or '/notmix/' in q:
            continue
        bn[os.path.basename(p)].append(p)

    def find_src(n):
        for b in (n + '.py', n + '_repro.py', n + '_variant.py', n + '_registered.py'):
            if b in bn and not EXCL.search(b):
                return bn[b][0], ''
        cs = [(b, ps[0]) for b, ps in bn.items()
              if (b == n + '.py' or b.startswith(n + '_')) and not EXCL.search(b)]
        if cs:
            return sorted(cs)[0][1], ''
        b0 = re.sub(r'_(prod|target)$', '', n)
        for b in (b0 + '_registered.py', b0 + '.py', b0 + '_repro.py'):
            if b in bn and not EXCL.search(b):
                return bn[b][0], 'SUBSTITUTED:%s' % b
        return None, 'MISSING'

    cases = []
    for n in r110_names:
        p, note = find_src(n)
        cases.append((n, p, note, 'R110'))
    mj = json.load(open(BASE + '/orandchain_if/matrix_v5r111_result.json', encoding='utf-8'))
    for c in mj['cases']:
        n = c['name']
        cases.append((n, MP + '/' + n + '.py', '', 'V111'))
    os.makedirs(CASEDIR, exist_ok=True)
    from r112_regress import V112_CASES
    from r113_regress import V113_CASES
    from matrix_v5r115 import CASES as V115_CASES
    from matrix_v5r116 import CASES as V116_CASES
    from matrix_v5r117 import CASES as V117_CASES
    for group, d in (('V112', V112_CASES), ('V113', V113_CASES),
                     ('V115', V115_CASES), ('V116', V116_CASES),
                     ('V117', V117_CASES), ('V118', V118_CASES), ('V119', V119_CASES),
                     ('V120', V120_CASES), ('V122', V122_CASES), ('V148', V148_CASES), ('V149', V149_CASES), ('V150', V150_CASES), ('V151', V151_CASES), ('V152', V152_CASES), ('V153', V153_CASES), ('V154', V154_CASES), ('V155', V155_CASES), ('V156', V156_CASES), ('V157', V157_CASES), ('V158', V158_CASES), ('V159', V159_CASES), ('V160', V160_CASES), ('V161', V161_CASES)):
        for n, src in d.items():
            p = CASEDIR + '/' + n + '.py'
            open(p, 'w', encoding='utf-8').write(src)
            cases.append((n, p, '', group))
    return cases, r110_names


def decompile(pyc, out, err):
    with open(out, 'wb') as fo, open(err, 'wb') as fe:
        r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', pyc],
                           stdout=fo, stderr=fe, cwd=REPO, timeout=300)
    return open(out, 'rb').read(), r.returncode


def parse_r110():
    out = {}
    for l in open(R110, encoding='utf-8'):
        if not l.strip() or l.startswith('TEXT-DIFF') or 'count' in l:
            continue
        parts = l.split(None, 2)
        out[parts[0]] = (parts[1], parts[2].strip() if len(parts) > 2 else '')
    return out


def ensure_v161():
    """启动自愈：若上次 A/B 交换被信号打断使文件停在 HEAD 版，
    断言失败提示（本轮自愈依赖工作树完好）。"""
    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    b3 = open(AC, 'rb').read()
    b4 = open(CG, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v155-CONDLEAK' in b
            and b'v153-RESIDUNPACK' in b2
            and b'v154-KWMERGE' in b3
            and b'v156-BINPAREN' in b4
            and b'v157-DELWIN' in b2
            and b'v158-RETFIN' in b2
            and b'v159-NOTCOND' in b
            and b'v160-DEEPRET' in b2
            and b'v161-NOTMIX' in b), \
        'v161 markers missing — work tree not on v161, abort (no self-heal this round)'
    return b


def decompile_cached(pyc, out):
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return open(out, 'rb').read()
    return decompile(pyc, out, out + '.err')[0]


START, END = 0, 10 ** 9


def main():
    head_rag = subprocess.run([GIT, '-C', REPO, 'show', HEAD + ':core/cfg/region_analyzer.py'],
                              capture_output=True).stdout
    head_rag2 = subprocess.run([GIT, '-C', REPO, 'show', HEAD + ':core/cfg/region_ast_generator.py'],
                               capture_output=True).stdout
    cur_rag = ensure_v161()
    cur_files = {p: open(p, 'rb').read() for p in V148_FILES}
    head_cg = subprocess.run([GIT, '-C', REPO, 'show', HEAD + ':core/cfg/code_generator.py'],
                             capture_output=True).stdout
    head_rag2 = subprocess.run([GIT, '-C', REPO, 'show', HEAD + ':core/cfg/region_ast_generator.py'],
                               capture_output=True).stdout
    head_rag = subprocess.run([GIT, '-C', REPO, 'show', HEAD + ':core/cfg/region_analyzer.py'],
                              capture_output=True).stdout
    head_rag2 = subprocess.run([GIT, '-C', REPO, 'show', HEAD + ':core/cfg/region_ast_generator.py'],
                               capture_output=True).stdout
    assert b'v160-DEEPRET' in head_rag2, 'HEAD generator should contain v160 patch'
    assert b'v159-NOTCOND' in head_rag, 'HEAD analyzer should contain v159 patch'
    assert b'v161-NOTMIX' not in head_rag, 'HEAD already contains v161 patch?'
    assert b'v158-RETFIN' in head_rag2, 'HEAD generator should contain v158 patch'
    assert b'v157-DELWIN' in head_rag2, 'HEAD generator should contain v157 patch'
    assert b'v156-BINPAREN' in head_cg, 'HEAD generator should contain v156 patch'
    assert b'v152-ORCLAIM' in head_rag, 'HEAD analyzer should contain v152 patch'
    assert b'v148-NOTTAIL' in head_rag2, 'HEAD generator should contain v148 patch'
    assert b'v149-NOTELIF' not in head_rag2, 'HEAD generator already contains v149 patch?'
    assert b'v145-ORNEST2' in head_rag2, 'HEAD generator should contain v145 patch'
    assert b'v152-ORCLAIM' in cur_rag, 'v152 analyzer markers missing'
    assert b'v161-NOTMIX' in cur_rag, 'v161 analyzer markers missing'
    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(OUTDIR_H, exist_ok=True)
    cases, _ = build_cases()
    r110 = parse_r110()

    prepared = []
    for name, src, note, grp in cases:
        if src is None or not os.path.exists(src):
            prepared.append((name, grp, note, None, None))
            continue
        pyc = OUTDIR + '/%s.pyc' % name
        py_compile.compile(src, cfile=pyc, doraise=True)
        prepared.append((name, grp, note, src, pyc))
    todo = [p for p in prepared if p[4] is not None]
    chunk = todo[START:END]

    for i, (name, grp, note, src, pyc) in enumerate(chunk, 1):
        decompile_cached(pyc, OUTDIR + '/%s.py' % name)
        if i % 40 == 0:
            print('[phase1] chunk %d/%d' % (i, len(chunk)), flush=True)
    print('[phase1] 本块 v161 产品就绪 %d/%d' % (len(chunk), len(chunk)), flush=True)

    head_files = {}
    for _vf in V148_FILES:
        _rel = _vf.replace(REPO + '/', '')
        head_files[_vf] = subprocess.run([GIT, '-C', REPO, 'show', HEAD + ':' + _rel],
                                         capture_output=True).stdout
    try:
        for _vf, _hb in head_files.items():
            open(_vf, 'wb').write(_hb)
        for i, (name, grp, note, src, pyc) in enumerate(chunk, 1):
            decompile_cached(pyc, OUTDIR_H + '/%s.py' % name)
            if i % 40 == 0:
                print('[phase2] chunk %d/%d' % (i, len(chunk)), flush=True)
    finally:
        for _vf, _cb in cur_files.items():
            open(_vf, 'wb').write(_cb)
        assert open(RAG, 'rb').read() == cur_files[RAG], 'analyzer not restored!'
        assert open(RAG2, 'rb').read() == cur_files[RAG2], 'generator not restored!'
    print('[phase2] 本块 HEAD 产品就绪 %d/%d，文件已恢复 v161' % (len(chunk), len(chunk)), flush=True)

    results = []
    for name, grp, note, src, pyc in prepared:
        if pyc is None:
            results.append((name, grp, note, 'NO-SRC', 'NO-SRC', ''))
            continue
        tv = open(OUTDIR + '/%s.py' % name, 'rb').read()
        th = open(OUTDIR_H + '/%s.py' % name, 'rb').read()
        ab = 'TEXT-SAME' if tv == th else 'TEXT-DIFF'
        st = fn_status(open(src, encoding='utf-8').read(), tv.decode('utf-8'))
        results.append((name, grp, note, ab, st, ''))

    lines = ['']
    for name, grp, note, ab, st, _ in results:
        lines.append('%-24s %-10s %s%s' % (name, ab, st,
                     ('  [%s]' % note) if note else ''))
    nd = sum(1 for r in results if r[3] == 'TEXT-DIFF')
    lines.append('')
    lines.append('TEXT-DIFF count: %d / %d' % (nd, len(results)))
    open(EV + '/r161_regress_result.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

    eq_text = eq_sig = 0
    cmp_rows = []
    for name, grp, note, ab, st, _ in results:
        if grp != 'R110':
            continue
        r_ab, r_st = r110.get(name, ('', ''))
        t_ok = (ab == r_ab); s_ok = (st == r_st)
        eq_text += t_ok; eq_sig += s_ok
        cmp_rows.append((name, note, r_ab, r_st, ab, st, t_ok, s_ok))
    print()
    print('R110 案: %d  TEXT 状态一致 %d  签名一致 %d' % (len(cmp_rows), eq_text, eq_sig))
    print()
    print('=== 既有登记差 10 案：r110 -> r161 逐字节同签名核验 ===')
    reg_ok = True
    subst_rows = []
    for name in REGISTERED:
        row = next((r for r in cmp_rows if r[0] == name), None)
        if row is None:
            print('  %-14s MISSING' % name); reg_ok = False; continue
        _, note, r_ab, r_st, ab, st, t_ok, s_ok = row
        substituted = note.startswith('SUBSTITUTED')
        if substituted and ab == 'TEXT-SAME' and not s_ok:
            subst_rows.append((name, note, r_st, st))
            tag, ok = 'SUBST-SIG(产品未变)', True
        else:
            ok = t_ok and s_ok and ab == 'TEXT-SAME'
            tag = 'SAME-SIG' if ok else 'CHANGED'
        reg_ok &= ok
        print('  %-14s %-22s %s' % (name, tag,
              ('%s | %s' % (r_st, st)) if not s_ok else r_st))
    print()
    if subst_rows:
        print('=== 语料替代案（早期清理后缺失，以等价源替代；A/B TEXT-SAME 实证产品逐字节未变）===')
        for n, note, r_st, st in subst_rows:
            print('  %-14s %s' % (n, note))
            print('      r110 签名: %s' % r_st)
            print('      r161 签名: %s' % st)
    print()
    print('REG-10: %s' % ('ALL SAME-SIGNATURE' if reg_ok else 'CHANGED !!'))
    # V148 案全列
    print()
    print('=== V148..V161 矩阵列 ===')
    for name, grp, note, ab, st, _ in results:
        if grp in ('V148', 'V149', 'V150', 'V151', 'V152', 'V153', 'V154', 'V155', 'V156', 'V157', 'V158', 'V159', 'V160', 'V161'):
            print('  %-18s %-10s %s' % (name, ab, st))
    # TEXT-DIFF 明细（若非 0，列案名供判读）
    if nd:
        print()
        print('=== TEXT-DIFF 明细 ===')
        for name, grp, note, ab, st, _ in results:
            if ab == 'TEXT-DIFF':
                print('  %-24s %-6s %s' % (name, grp, st))


if __name__ == '__main__':
    main()
