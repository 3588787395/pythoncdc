# derive156.py: r155_regress.py -> binparen/r156_regress.py (rr-v5r156 battery, 5-file swap)
import io, os

SRC = r'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/condleak/r155_regress.py'
DST_DIR = r'F:/Downloads/pythoncdc-main/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/binparen'
DST = DST_DIR + '/r156_regress.py'
os.makedirs(DST_DIR, exist_ok=True)

s = io.open(SRC, encoding='utf-8').read()

old_hdr = """# rr-v5r155 [v155-CONDLEAK] A/B 回归电池（368 案；五文件交换）
#   以 r154_regress.py 为模板：R110 169 案 + V111..V122/V148..V154 累计案 + V155 矩阵 11 案。
#   逐案 compile -> pyc -> decompile CURRENT(v155) 与 HEAD(09b4d4b8) 版
#   （git-show 五文件交换：analyzer/generator/ast_nodes/ast_converter/code_generator）
#   -> 比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r155regress/（独立 TMP，干净重跑）。"""
assert old_hdr in s, 'hdr'
new_hdr = """# rr-v5r156 [v156-BINPAREN] A/B 回归电池（385 案；五文件交换）
#   以 r155_regress.py 为模板：R110 169 案 + V111..V122/V148..V155 累计案 + V156 矩阵 17 案。
#   逐案 compile -> pyc -> decompile CURRENT(v156) 与 HEAD(4a2208e6) 版
#   （git-show 五文件交换：analyzer/generator/ast_nodes/ast_converter/code_generator）
#   -> 比产品文本(A/B) + 重编译签名。
#   中间产物写 D:/temp/opencode/cl_layout/r156regress/（独立 TMP，干净重跑）。"""
s = s.replace(old_hdr, new_hdr, 1)

assert "BASE + '/condleak'" in s
s = s.replace("BASE + '/condleak'", "BASE + '/binparen'", 1)
assert "r155regress" in s
s = s.replace("r155regress", "r156regress", 1)
assert "OUTDIR = TMP + '/v155'" in s
s = s.replace("OUTDIR = TMP + '/v155'", "OUTDIR = TMP + '/v156'", 1)
assert "HEAD = '09b4d4b8'" in s
s = s.replace("HEAD = '09b4d4b8'", "HEAD = '4a2208e6'", 1)

assert "or '/condleak/' in q:" in s
s = s.replace("or '/condleak/' in q:", "or '/condleak/' in q or '/binparen/' in q:", 1)

# markers: code_generator v156-BINPAREN + v154-KWMERGE
old_ensure = """    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    b3 = open(AC, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v155-CONDLEAK' in b
            and b'v153-RESIDUNPACK' in b2
            and b'v154-KWMERGE' in b3), \\
        'v155 markers missing — work tree not on v155, abort (no self-heal this round)'
    return b"""
assert old_ensure in s, 'ensure'
new_ensure = """    b = open(RAG, 'rb').read()
    b2 = open(RAG2, 'rb').read()
    b3 = open(AC, 'rb').read()
    assert (b'v152-ORCLAIM' in b and b'v152-LATCH' in b
            and b'v155-CONDLEAK' in b
            and b'v153-RESIDUNPACK' in b2
            and b'v154-KWMERGE' in b3
            and b'v156-BINPAREN' in b3), \\
        'v156 markers missing — work tree not on v156, abort (no self-heal this round)'
    return b"""
s = s.replace(old_ensure, new_ensure, 1)

old_a = """    assert b'v155-CONDLEAK' not in head_rag, 'HEAD already contains v155 patch?'
    assert b'v152-ORCLAIM' in head_rag, 'HEAD analyzer should contain v152 patch'"""
assert old_a in s, 'main-a'
new_a = """    assert b'v156-BINPAREN' not in head_rag, 'HEAD already contains v156 patch?'
    assert b'v152-ORCLAIM' in head_rag, 'HEAD analyzer should contain v152 patch'"""
s = s.replace(old_a, new_a, 1)
old_b = "    assert b'v152-ORCLAIM' in cur_rag, 'v152 analyzer markers missing'"
assert old_b in s, 'main-b'
s = s.replace(old_b, "    assert b'v152-ORCLAIM' in cur_rag, 'v152 analyzer markers missing'", 1)

anchor_excl = "\nEXCL = re.compile("
assert anchor_excl in s
v156_block = '''

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

'''
s = s.replace(anchor_excl, v156_block + "\nEXCL = re.compile(", 1)

assert "('V155', V155_CASES)):" in s
s = s.replace("('V155', V155_CASES)):", "('V155', V155_CASES), ('V156', V156_CASES)):", 1)

s = s.replace("cur_rag = ensure_v155()", "cur_rag = ensure_v156()", 1)
s = s.replace("def ensure_v155():", "def ensure_v156():", 1)

s = s.replace("本块 v155 产品就绪", "本块 v156 产品就绪")
s = s.replace("文件已恢复 v155", "文件已恢复 v156")
assert "r155_regress_result.txt" in s
s = s.replace("r155_regress_result.txt", "r156_regress_result.txt", 1)
s = s.replace("r110 -> r155 逐字节同签名核验", "r110 -> r156 逐字节同签名核验")
s = s.replace("r155 签名: %s", "r156 签名: %s")
s = s.replace("=== V148..V155 矩阵列 ===", "=== V148..V156 矩阵列 ===")
s = s.replace("if grp in ('V148', 'V149', 'V150', 'V151', 'V152', 'V153', 'V154', 'V155'):",
              "if grp in ('V148', 'V149', 'V150', 'V151', 'V152', 'V153', 'V154', 'V155', 'V156'):")

io.open(DST, 'w', encoding='utf-8').write(s)
print('derived r156_regress.py ->', DST)

import py_compile
py_compile.compile(DST, doraise=True)
print('syntax OK')
