# derive154.py: r153_regress.py -> kwmerge/r154_regress.py (rr-v5r154 battery, 5-file swap)
import io, os

SRC = r'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/residunpack/r153_regress.py'
DST_DIR = r'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/kwmerge'
DST = DST_DIR + '/r154_regress.py'
os.makedirs(DST_DIR, exist_ok=True)

s = io.open(SRC, encoding='utf-8').read()

old_hdr = """# rr-v5r153 [v153-RESIDUNPACK] A/B 回归电池（341 案）
#   以 r152_regress.py 为模板：R110 169 案 + V111..V122/V148..V152 累计案 + V153 矩阵 19 案。
#   逐案 compile -> pyc -> decompile CURRENT(v153) 与 HEAD(789e15b7) 版
#   （git-show 双文件交换）-> 比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r153regress/（独立 TMP，干净重跑）。"""
assert old_hdr in s, 'hdr'
new_hdr = """# rr-v5r154 [v154-KWMERGE] A/B 回归电池（357 案；五文件交换）
#   以 r153_regress.py 为模板：R110 169 案 + V111..V122/V148..V153 累计案 + V154 矩阵 16 案。
#   逐案 compile -> pyc -> decompile CURRENT(v154) 与 HEAD(254d2751) 版
#   （git-show 五文件交换：analyzer/generator/ast_nodes/ast_converter/code_generator）
#   -> 比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r154regress/（独立 TMP，干净重跑）。"""
s = s.replace(old_hdr, new_hdr, 1)

assert "BASE + '/residunpack'" in s
s = s.replace("BASE + '/residunpack'", "BASE + '/kwmerge'", 1)
assert "r153regress" in s
s = s.replace("r153regress", "r154regress", 1)
assert "OUTDIR = TMP + '/v153'" in s
s = s.replace("OUTDIR = TMP + '/v153'", "OUTDIR = TMP + '/v154'", 1)
assert "HEAD = '789e15b7'" in s
s = s.replace("HEAD = '789e15b7'", "HEAD = '254d2751'", 1)

assert "or '/residunpack/' in q:" in s
s = s.replace("or '/residunpack/' in q:", "or '/residunpack/' in q or '/kwmerge/' in q:", 1)

# --- five-file swap: extend V153_FILES/V148_FILES machinery ---
old_files = """RAG = REPO + '/core/cfg/region_analyzer.py'
RAG2 = REPO + '/core/cfg/region_ast_generator.py'
V148_FILES = (RAG, RAG2)"""
assert old_files in s, 'files decl'
new_files = """RAG = REPO + '/core/cfg/region_analyzer.py'
RAG2 = REPO + '/core/cfg/region_ast_generator.py'
# [v154-KWMERGE] 本轮改动三文件并入交换集（五文件 A/B）
AN = REPO + '/core/ast_nodes.py'
AC = REPO + '/core/cfg/ast_converter.py'
CG = REPO + '/core/cfg/code_generator.py'
V148_FILES = (RAG, RAG2, AN, AC, CG)"""
s = s.replace(old_files, new_files, 1)

# ensure: generator marker v153-RESIDUNPACK + converter marker v154-KWMERGE
old_ensure = """    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v153-RESIDUNPACK' in b2), \\
        'v153 markers missing — work tree not on v153, abort (no self-heal this round)'
    return b"""
assert old_ensure in s, 'ensure'
new_ensure = """    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    b3 = open(AC, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v153-RESIDUNPACK' in b2
            and b'v154-KWMERGE' in b3), \\
        'v154 markers missing — work tree not on v154, abort (no self-heal this round)'
    return b"""
s = s.replace(old_ensure, new_ensure, 1)

# main asserts: HEAD must not contain v154 in converter
old_a = """    assert b'v153-RESIDUNPACK' not in head_rag, 'HEAD already contains v153 patch?'
    assert b'v152-ORCLAIM' in head_rag, 'HEAD analyzer should contain v152 patch'"""
assert old_a in s, 'main-a'
new_a = """    assert b'v154-KWMERGE' not in subprocess.run([GIT, '-C', REPO, 'show',
        HEAD + ':core/cfg/ast_converter.py'], capture_output=True).stdout, \\
        'HEAD already contains v154 patch?'
    assert b'v152-ORCLAIM' in head_rag, 'HEAD analyzer should contain v152 patch'"""
s = s.replace(old_a, new_a, 1)

anchor_excl = "\nEXCL = re.compile("
assert anchor_excl in s
v154_block = '''

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

'''
s = s.replace(anchor_excl, v154_block + "\nEXCL = re.compile(", 1)

assert "('V153', V153_CASES)):" in s
s = s.replace("('V153', V153_CASES)):", "('V153', V153_CASES), ('V154', V154_CASES)):", 1)

# rename ensure function call
s = s.replace("cur_rag = ensure_v153()", "cur_rag = ensure_v154()", 1)
s = s.replace("def ensure_v153():", "def ensure_v154():", 1)

# phase prints / result file
s = s.replace("本块 v153 产品就绪", "本块 v154 产品就绪")
s = s.replace("文件已恢复 v153", "文件已恢复 v154")
assert "r153_regress_result.txt" in s
s = s.replace("r153_regress_result.txt", "r154_regress_result.txt", 1)
s = s.replace("r110 -> r153 逐字节同签名核验", "r110 -> r154 逐字节同签名核验")
s = s.replace("r153 签名: %s", "r154 签名: %s")
s = s.replace("=== V148..V153 矩阵列 ===", "=== V148..V154 矩阵列 ===")
s = s.replace("if grp in ('V148', 'V149', 'V150', 'V151', 'V152', 'V153'):",
              "if grp in ('V148', 'V149', 'V150', 'V151', 'V152', 'V153', 'V154'):")

io.open(DST, 'w', encoding='utf-8').write(s)
print('derived r154_regress.py ->', DST)

import py_compile
py_compile.compile(DST, doraise=True)
print('syntax OK')
