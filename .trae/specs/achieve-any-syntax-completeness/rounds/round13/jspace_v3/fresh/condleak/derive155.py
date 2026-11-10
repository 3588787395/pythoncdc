# derive155.py: r154_regress.py -> condleak/r155_regress.py (rr-v5r155 battery, 5-file swap)
import io, os

SRC = r'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/kwmerge/r154_regress.py'
DST_DIR = r'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/condleak'
DST = DST_DIR + '/r155_regress.py'
os.makedirs(DST_DIR, exist_ok=True)

s = io.open(SRC, encoding='utf-8').read()

old_hdr = """# rr-v5r154 [v154-KWMERGE] A/B 回归电池（357 案；五文件交换）
#   以 r153_regress.py 为模板：R110 169 案 + V111..V122/V148..V153 累计案 + V154 矩阵 16 案。
#   逐案 compile -> pyc -> decompile CURRENT(v154) 与 HEAD(254d2751) 版
#   （git-show 五文件交换：analyzer/generator/ast_nodes/ast_converter/code_generator）
#   -> 比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r154regress/（独立 TMP，干净重跑）。"""
assert old_hdr in s, 'hdr'
new_hdr = """# rr-v5r155 [v155-CONDLEAK] A/B 回归电池（368 案；五文件交换）
#   以 r154_regress.py 为模板：R110 169 案 + V111..V122/V148..V154 累计案 + V155 矩阵 11 案。
#   逐案 compile -> pyc -> decompile CURRENT(v155) 与 HEAD(09b4d4b8) 版
#   （git-show 五文件交换：analyzer/generator/ast_nodes/ast_converter/code_generator）
#   -> 比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r155regress/（独立 TMP，干净重跑）。"""
s = s.replace(old_hdr, new_hdr, 1)

assert "BASE + '/kwmerge'" in s
s = s.replace("BASE + '/kwmerge'", "BASE + '/condleak'", 1)
assert "r154regress" in s
s = s.replace("r154regress", "r155regress", 1)
assert "OUTDIR = TMP + '/v154'" in s
s = s.replace("OUTDIR = TMP + '/v154'", "OUTDIR = TMP + '/v155'", 1)
assert "HEAD = '254d2751'" in s
s = s.replace("HEAD = '254d2751'", "HEAD = '09b4d4b8'", 1)

assert "or '/kwmerge/' in q:" in s
s = s.replace("or '/kwmerge/' in q:", "or '/kwmerge/' in q or '/condleak/' in q:", 1)

# markers: analyzer v155-CONDLEAK + v152-ORCLAIM
old_ensure = """    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    b3 = open(AC, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v153-RESIDUNPACK' in b2
            and b'v154-KWMERGE' in b3), \\
        'v154 markers missing — work tree not on v154, abort (no self-heal this round)'
    return b"""
assert old_ensure in s, 'ensure'
new_ensure = """    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    b3 = open(AC, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v155-CONDLEAK' in b
            and b'v153-RESIDUNPACK' in b2
            and b'v154-KWMERGE' in b3), \\
        'v155 markers missing — work tree not on v155, abort (no self-heal this round)'
    return b"""
s = s.replace(old_ensure, new_ensure, 1)

old_a = """    assert b'v154-KWMERGE' not in subprocess.run([GIT, '-C', REPO, 'show',
        HEAD + ':core/cfg/ast_converter.py'], capture_output=True).stdout, \\
        'HEAD already contains v154 patch?'
    assert b'v152-ORCLAIM' in head_rag, 'HEAD analyzer should contain v152 patch'"""
assert old_a in s, 'main-a'
new_a = """    assert b'v155-CONDLEAK' not in head_rag, 'HEAD already contains v155 patch?'
    assert b'v152-ORCLAIM' in head_rag, 'HEAD analyzer should contain v152 patch'"""
s = s.replace(old_a, new_a, 1)
old_b = "    assert b'v152-ORCLAIM' in cur_rag, 'v152 analyzer markers missing'"
assert old_b in s, 'main-b'
s = s.replace(old_b, "    assert b'v152-ORCLAIM' in cur_rag, 'v152 analyzer markers missing'", 1)

anchor_excl = "\nEXCL = re.compile("
assert anchor_excl in s
v155_block = '''

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

'''
s = s.replace(anchor_excl, v155_block + "\nEXCL = re.compile(", 1)

assert "('V154', V154_CASES)):" in s
s = s.replace("('V154', V154_CASES)):", "('V154', V154_CASES), ('V155', V155_CASES)):", 1)

s = s.replace("cur_rag = ensure_v154()", "cur_rag = ensure_v155()", 1)
s = s.replace("def ensure_v154():", "def ensure_v155():", 1)

s = s.replace("本块 v154 产品就绪", "本块 v155 产品就绪")
s = s.replace("文件已恢复 v154", "文件已恢复 v155")
assert "r154_regress_result.txt" in s
s = s.replace("r154_regress_result.txt", "r155_regress_result.txt", 1)
s = s.replace("r110 -> r154 逐字节同签名核验", "r110 -> r155 逐字节同签名核验")
s = s.replace("r154 签名: %s", "r155 签名: %s")
s = s.replace("=== V148..V154 矩阵列 ===", "=== V148..V155 矩阵列 ===")
s = s.replace("if grp in ('V148', 'V149', 'V150', 'V151', 'V152', 'V153', 'V154'):",
              "if grp in ('V148', 'V149', 'V150', 'V151', 'V152', 'V153', 'V154', 'V155'):")

io.open(DST, 'w', encoding='utf-8').write(s)
print('derived r155_regress.py ->', DST)

import py_compile
py_compile.compile(DST, doraise=True)
print('syntax OK')
