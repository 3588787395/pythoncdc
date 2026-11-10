# derive153.py: r152_regress.py -> mdiff/r153_regress.py (rr-v5r153 battery)
import io, os

SRC = r'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/mdiff/r152_regress.py'
DST_DIR = r'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/residunpack'
DST = DST_DIR + '/r153_regress.py'
os.makedirs(DST_DIR, exist_ok=True)

s = io.open(SRC, encoding='utf-8').read()

old_hdr = """# rr-v5r152 [v152-HANDLERRET/ORCLAIM/LATCH/DUALUNPACK2] A/B 回归电池（326 案）
#   以 r151_regress.py 为模板：R110 169 案 + V111..V122/V148..V151 累计案 + V152 矩阵 15 案。
#   逐案 compile -> pyc -> decompile CURRENT(v152) 与 HEAD(dda01bb9) 版
#   （git-show 双文件交换）-> 比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r152regress/（独立 TMP，干净重跑）。"""
assert old_hdr in s, 'hdr'
new_hdr = """# rr-v5r153 [v153-RESIDUNPACK] A/B 回归电池（341 案）
#   以 r152_regress.py 为模板：R110 169 案 + V111..V122/V148..V152 累计案 + V153 矩阵 19 案。
#   逐案 compile -> pyc -> decompile CURRENT(v153) 与 HEAD(789e15b7) 版
#   （git-show 双文件交换）-> 比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r153regress/（独立 TMP，干净重跑）。"""
s = s.replace(old_hdr, new_hdr, 1)

assert "BASE + '/mdiff'" in s
s = s.replace("BASE + '/mdiff'", "BASE + '/residunpack'", 1)
assert "r152regress" in s
s = s.replace("r152regress", "r153regress", 1)
assert "OUTDIR = TMP + '/v152'" in s
s = s.replace("OUTDIR = TMP + '/v152'", "OUTDIR = TMP + '/v153'", 1)
assert "HEAD = 'dda01bb9'" in s
s = s.replace("HEAD = 'dda01bb9'", "HEAD = '789e15b7'", 1)

assert "or '/mdiff/' in q:" in s
s = s.replace("or '/mdiff/' in q:", "or '/mdiff/' in q or '/residunpack/' in q:", 1)

anchor_excl = "\nEXCL = re.compile("
assert anchor_excl in s
v153_block = '''

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

'''
s = s.replace(anchor_excl, v153_block + "\nEXCL = re.compile(", 1)

assert "('V152', V152_CASES)):" in s
s = s.replace("('V152', V152_CASES)):", "('V152', V152_CASES), ('V153', V153_CASES)):", 1)

old_ensure = """def ensure_v152():
    \"\"\"启动自愈：若上次 A/B 交换被信号打断使文件停在 HEAD 版，
    断言失败提示（本轮自愈依赖工作树完好）。\"\"\"
    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v152-HANDLERRET' in b2), \\
        'v152 markers missing — work tree not on v152, abort (no self-heal this round)'
    return b"""
assert old_ensure in s, 'ensure'
new_ensure = """def ensure_v153():
    \"\"\"启动自愈：若上次 A/B 交换被信号打断使文件停在 HEAD 版，
    断言失败提示（本轮自愈依赖工作树完好）。\"\"\"
    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v153-RESIDUNPACK' in b2), \\
        'v153 markers missing — work tree not on v153, abort (no self-heal this round)'
    return b"""
s = s.replace(old_ensure, new_ensure, 1)
assert "cur_rag = ensure_v152()" in s
s = s.replace("cur_rag = ensure_v152()", "cur_rag = ensure_v153()", 1)

old_a = """    assert b'v152-ORCLAIM' not in head_rag, 'HEAD already contains v152 patch?'
    assert b'v151-OUTERYIELD' in head_rag, 'HEAD analyzer should contain v151 patch'"""
assert old_a in s, 'main-a'
new_a = """    assert b'v153-RESIDUNPACK' not in head_rag, 'HEAD already contains v153 patch?'
    assert b'v152-ORCLAIM' in head_rag, 'HEAD analyzer should contain v152 patch'"""
s = s.replace(old_a, new_a, 1)
old_b = "    assert b'v152-ORCLAIM' in cur_rag, 'v152 analyzer markers missing'"
assert old_b in s, 'main-b'
s = s.replace(old_b, "    assert b'v152-ORCLAIM' in cur_rag, 'v152 analyzer markers missing'", 1)

s = s.replace("本块 v152 产品就绪", "本块 v153 产品就绪")
s = s.replace("文件已恢复 v152", "文件已恢复 v153")
assert "r152_regress_result.txt" in s
s = s.replace("r152_regress_result.txt", "r153_regress_result.txt", 1)
s = s.replace("r110 -> r152 逐字节同签名核验", "r110 -> r153 逐字节同签名核验")
s = s.replace("r152 签名: %s", "r153 签名: %s")
s = s.replace("=== V148..V152 矩阵列 ===", "=== V148..V153 矩阵列 ===")
s = s.replace("if grp in ('V148', 'V149', 'V150', 'V151', 'V152'):", "if grp in ('V148', 'V149', 'V150', 'V151', 'V152', 'V153'):")

io.open(DST, 'w', encoding='utf-8').write(s)
print('derived r153_regress.py ->', DST)

import py_compile
py_compile.compile(DST, doraise=True)
print('syntax OK')
