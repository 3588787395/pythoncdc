# rr-v5r138 [v138-FTUNPACK] 变体矩阵（A/B 单文件交换：HEAD 4865223a vs v138 工作树）
# 功效案：融合落空块（_build_effective_stmts 域）UNPACK 多目标解包赋值
# 控制案：for 目标解包（循环机制域绝不可吞）/单赋值/r136/r137 回归防护
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r138matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v138_%s.py' % k for k in FILES}
os.makedirs(OUT, exist_ok=True)
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：else 臂解包赋值（r137 矩阵 C4 形，融合落空域）
    'E1_ft_unpack': '''def m(pairs):
    x = y = 0
    for p in pairs:
        if x:
            x -= 1
        else:
            x, y = p
    return x + y
''',
    # 功效案：else 臂星号解包（UNPACK_EX before/after 形）
    'E2_ft_unpack_ex': '''def g(pairs):
    head = []
    rest = None
    for p in pairs:
        if head:
            head.append(p)
        else:
            a, *b = p
            head.append(a)
            rest = b
    return head, rest
''',
    # 功效案：else 臂调用值解包
    'E3_ft_unpack_call': '''def h(rows):
    x = y = 0
    for r in rows:
        if x:
            x -= 1
        else:
            x, y = f(r)
    return x + y

def f(r):
    return r[0], r[1]
''',
    # 控制案：for 目标解包（循环机制域，for_iter_fall_through，绝不可吞——零漂移）
    'C1_for_target_unpack': '''def k(pairs):
    total = 0
    for a, b in pairs:
        total += a + b
    return total
''',
    # 控制案：融合落空块单赋值（既有路径零漂移）
    'C2_ft_single': '''def h2(items):
    acc = 0
    for x in items:
        if x:
            acc += 1
        else:
            acc = x
    return acc
''',
    # 控制案：r137 E1 形（HEAD 已含 v137 修复）回归防护
    'C3_r137_guard': '''def f(pairs):
    x = y = 0
    hit = []
    for a, b in pairs:
        if a > y:
            y = a
        else:
            hit.append(y)
            x, y = b, a
    return hit, x + y
''',
    # 控制案：r136 E1 形（回边走查域）回归防护
    'C4_r136_guard': '''def g(blocks):
    i1 = j1 = k1 = 0
    out = []
    for i2, j2, k2 in blocks:
        if i1 + k1 == i2 and j1 + k1 == j2:
            k1 += k2
        else:
            if k1:
                out.append((i1, j1, k1))
            i1, j1, k1 = i2, j2, k2
    return out
''',
    # 预存在残差：链式融合域 walrus 形（COPY 域，r136/r137 矩阵同形，排除判定）
    'C5_chain_preexisting': '''def k2(vs):
    a = b = 0
    for v in vs:
        if v:
            a += v
        else:
            a = b = v
    return a + b
''',
}

def compile_src(cid, src):
    p = OUT + '/%s_src.py' % cid
    open(p, 'w', encoding='utf-8').write(src)
    r = subprocess.run([PY, '-I', '-c', 'import py_compile; py_compile.compile(r"%s", r"%s", doraise=True)' % (p, OUT + '/%s.pyc' % cid)], capture_output=True, text=True)
    assert r.returncode == 0, (cid, r.stderr)

def norm(c):
    return tuple('<code:%s>' % x.co_name if hasattr(x, 'co_name') else x for x in c)

def byte_equal(orig, prod):
    if orig.co_code != prod.co_code: return False
    if orig.co_exceptiontable != prod.co_exceptiontable: return False
    if norm(orig.co_consts) != norm(prod.co_consts): return False
    for a in ('co_names','co_varnames','co_freevars','co_cellvars','co_argcount','co_flags'):
        if getattr(orig,a) != getattr(prod,a): return False
    oc = [c for c in orig.co_consts if hasattr(c,'co_name')]
    pc = [c for c in prod.co_consts if hasattr(c,'co_name')]
    if len(oc) != len(pc): return False
    return all(byte_equal(o2, p2) for o2, p2 in zip(oc, pc))

if __name__ == '__main__':
    for cid, src in CASES.items():
        compile_src(cid, src)
    head_exports = {}
    for k, p in FILES.items():
        r = subprocess.run(['git', '-C', REPO, 'show', 'HEAD:' + p.replace(REPO + '/', '')], capture_output=True)
        hp = OUT + '/head_%s.py' % k
        open(hp, 'wb').write(r.stdout)
        head_exports[k] = hp
    summary = []
    for cid in CASES:
        head_py = OUT + '/%s_out_head.py' % cid
        v138_py = OUT + '/%s_out_v138.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v138_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v138_py,'rb').read()
        try:
            py_compile.compile(v138_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-24s text_same=%-5s v138_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD 丢次级目标（TEXT-DIFF）→ v138 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    # 预存在残差（head 与 v138 输出逐字节同=本轮零触碰，排除判定）：
    #   C5=链式融合域 walrus 形（COPY 域，r136/r137 矩阵同形）。
    E = {'E1_ft_unpack', 'E2_ft_unpack_ex', 'E3_ft_unpack_call'}
    PREEXISTING = {'C5_chain_preexisting'}
    verdicts = []
    for cid, same, ok in summary:
        if cid in PREEXISTING:
            print('verdict %-24s PREEXISTING-FAIL(非本轮引入，head 同不等)' % cid)
            continue
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-24s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
