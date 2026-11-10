# derive152.py: r151_regress.py -> mdiff/r152_regress.py (rr-v5r152 battery)
import io, os

SRC = r'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/outeryield/r151_regress.py'
DST_DIR = r'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/mdiff'
DST = DST_DIR + '/r152_regress.py'
os.makedirs(DST_DIR, exist_ok=True)

s = io.open(SRC, encoding='utf-8').read()

# --- header ---
old_hdr = """# rr-v5r151 [v151-OUTERYIELD] A/B 回归电池（311 案）
#   以 r150_regress.py 为模板：R110 169 案 + V111..V122/V148/V149/V150 累计案 + V151 矩阵 10 案。
#   逐案 compile -> pyc -> decompile CURRENT(v151) 与 HEAD(fe5ec72c) 版
#   （git-show 双文件交换）-> 比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r151regress/（独立 TMP，干净重跑）。"""
assert old_hdr in s, 'hdr'
new_hdr = """# rr-v5r152 [v152-HANDLERRET/ORCLAIM/LATCH/DUALUNPACK2] A/B 回归电池（326 案）
#   以 r151_regress.py 为模板：R110 169 案 + V111..V122/V148..V151 累计案 + V152 矩阵 15 案。
#   逐案 compile -> pyc -> decompile CURRENT(v152) 与 HEAD(dda01bb9) 版
#   （git-show 双文件交换）-> 比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r152regress/（独立 TMP，干净重跑）。"""
s = s.replace(old_hdr, new_hdr, 1)

# --- paths / HEAD ---
assert "BASE + '/outeryield'" in s
s = s.replace("BASE + '/outeryield'", "BASE + '/mdiff'", 1)
assert "r151regress" in s
s = s.replace("r151regress", "r152regress", 1)
assert "OUTDIR = TMP + '/v151'" in s
s = s.replace("OUTDIR = TMP + '/v151'", "OUTDIR = TMP + '/v152'", 1)
assert "HEAD = 'fe5ec72c'" in s
s = s.replace("HEAD = 'fe5ec72c'", "HEAD = 'dda01bb9'", 1)

# --- EXCL ---
assert "or '/outeryield/' in q:" in s
s = s.replace("or '/outeryield/' in q:", "or '/outeryield/' in q or '/mdiff/' in q:", 1)

# --- V152 cases before EXCL ---
anchor_excl = "\nEXCL = re.compile("
assert anchor_excl in s
v152_block = '''

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

'''
s = s.replace(anchor_excl, v152_block + "\nEXCL = re.compile(", 1)

# --- group loop ---
assert "('V151', V151_CASES)):" in s
s = s.replace("('V151', V151_CASES)):", "('V151', V151_CASES), ('V152', V152_CASES)):", 1)

# --- ensure function ---
old_ensure = """def ensure_v151():
    \"\"\"启动自愈：若上次 A/B 交换被信号打断使文件停在 HEAD 版，
    断言失败提示（本轮自愈依赖工作树完好）。\"\"\"
    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    assert b'v151-OUTERYIELD' in b and b'v148-NOTTAIL' in b2, \\
        'v151 markers missing — work tree not on v151, abort (no self-heal this round)'
    return b"""
assert old_ensure in s, 'ensure'
new_ensure = """def ensure_v152():
    \"\"\"启动自愈：若上次 A/B 交换被信号打断使文件停在 HEAD 版，
    断言失败提示（本轮自愈依赖工作树完好）。\"\"\"
    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v152-HANDLERRET' in b2), \\
        'v152 markers missing — work tree not on v152, abort (no self-heal this round)'
    return b"""
s = s.replace(old_ensure, new_ensure, 1)
assert "cur_rag = ensure_v151()" in s
s = s.replace("cur_rag = ensure_v151()", "cur_rag = ensure_v152()", 1)

# --- main assertions ---
old_a = """    assert b'v151-OUTERYIELD' not in head_rag, 'HEAD already contains v151 patch?'
    assert b'v150-RAISETERM' in head_rag, 'HEAD analyzer should contain v150 patch'"""
assert old_a in s, 'main-a'
new_a = """    assert b'v152-ORCLAIM' not in head_rag, 'HEAD already contains v152 patch?'
    assert b'v151-OUTERYIELD' in head_rag, 'HEAD analyzer should contain v151 patch'"""
s = s.replace(old_a, new_a, 1)
old_b = "    assert b'v151-OUTERYIELD' in cur_rag, 'v151 analyzer markers missing'"
assert old_b in s, 'main-b'
s = s.replace(old_b, "    assert b'v152-ORCLAIM' in cur_rag, 'v152 analyzer markers missing'", 1)

# --- phase prints / result file ---
s = s.replace("本块 v151 产品就绪", "本块 v152 产品就绪")
s = s.replace("文件已恢复 v151", "文件已恢复 v152")
assert "r151_regress_result.txt" in s
s = s.replace("r151_regress_result.txt", "r152_regress_result.txt", 1)
s = s.replace("r110 -> r151 逐字节同签名核验", "r110 -> r152 逐字节同签名核验")
s = s.replace("r151 签名: %s", "r152 签名: %s")
s = s.replace("=== V148/V149/V150/V151 矩阵列 ===", "=== V148..V152 矩阵列 ===")
s = s.replace("if grp in ('V148', 'V149', 'V150', 'V151'):", "if grp in ('V148', 'V149', 'V150', 'V151', 'V152'):")

io.open(DST, 'w', encoding='utf-8').write(s)
print('derived r152_regress.py ->', DST)

import py_compile
py_compile.compile(DST, doraise=True)
print('syntax OK')
