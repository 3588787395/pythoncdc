# rr-v5r145 [v145-ORNEST2] 变体矩阵（A/B 单文件交换：HEAD 3597cb33 vs v145 工作树）
# 功效案：多块 and 头嵌套链（E2）+ D1 守卫误触发回归修复（v144 引入，本轮域内闭合）
# 控制案：na5/r143 or 链/r142 and 链/r141 自环/r139 自环体 回归防护
# 预存在案：D3 守卫+嵌套（守卫 if 外提族，head==v145 逐字节同）、C3 扁平 and-or
import os, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r145matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    # 功效案 1：E2 多块 and 头嵌套链（v144 单块限定让位族）
    'E1_multi_and_or_nest': '''def g(a, b, c, f):
    i = 1
    while i < 10 and a[i] and (b[i] or f(i)):
        i += 1
    return i
''',
    # 功效案 2：D1 if 守卫 + 纯 or while（v144 既有误触发=真实 R1，本轮域内闭合）
    'E2_guard_or_while': '''def f(a, b, c):
    if a:
        while b or c:
            b -= 1
    return a
''',
    # 控制案：na5（v144 功效案，v145 回边复核判别下必须维持）
    'C1_na5': '''def f(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
''',
    # 控制案：r143 纯 or 链
    'C2_or2': '''def c2(a, b):
    i = 0
    while i > 3 or b[i] == 1:
        i += 1
    return i
''',
    # 控制案：r142 4 首 and 链
    'C3_and4': '''def w(a, b, isj, alo, blo, ahi, bhi):
    besti, bestj, bestsize = alo, blo, 0
    while besti > alo and bestj > blo and not isj(b[bestj - 1]) and a[besti - 1] == b[bestj - 1]:
        besti, bestj, bestsize = besti - 1, bestj - 1, bestsize + 1
    return besti, bestj, bestsize
''',
    # 控制案：r141 自环 B234
    'C4_r141': '''def w(items):
    besti = bestj = 0
    while items:
        besti, bestj = besti - 1, bestj - 1
        items.pop()
    return besti, bestj
''',
    # 控制案：r139 自环体
    'C5_r139': '''def m(items):
    res = []
    while items:
        a, b = items.pop()
        res.append(a + b)
    return res
''',
    # 预存在案：D3 守卫 + 嵌套 and+(or)（守卫 if 外提族，head 行为，本轮零触碰）
    'P1_guard_nest': '''def f(a, b, c, d):
    if a:
        while b and (c or d):
            b -= 1
    return a
''',
    # 预存在案：C3 扁平 and-or（假边目标不同族，登记）
    'P2_flat_and_or': '''def h(a, b, c):
    i = 0
    while i < 5 and b[i] or c[i]:
        i += 1
    return i
''',
    # 预存在案：D4 守卫多块 + or while（v144 经 _on_ext 幸存=正确渲染，维持）
    'P3_guard_multi_or': '''def f(a, b, c, d, e):
    if a < 10 and b[0]:
        while c[i2] or d(i2):
            i2 += 1
    return a
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
    FILES = {'RA': REPO + '/core/cfg/region_analyzer.py',
             'RAG': REPO + '/core/cfg/region_ast_generator.py'}
    for k, p in FILES.items():
        shutil.copy(p, OUT + '/v145_%s.py' % k)
    head_exports = {}
    for k, p in FILES.items():
        r = subprocess.run(['git', '-C', REPO, 'show', '3597cb33:' + p.replace(REPO + '/', '')], capture_output=True)
        hp = OUT + '/head_%s.py' % k
        open(hp, 'wb').write(r.stdout)
        head_exports[k] = hp
    summary = []
    for cid in CASES:
        head_py = OUT + '/%s_out_head.py' % cid
        v145_py = OUT + '/%s_out_v145.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(OUT + '/v145_%s.py' % k, p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v145_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v145_py,'rb').read()
        try:
            py_compile.compile(v145_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-24s text_same=%-5s v145_byte_equal=%s' % (cid, same, ok))
    # 功效案：E1（HEAD TEXT-DIFF→v145 BYTE-EQUAL）、E2（HEAD TEXT-DIFF→v145 BYTE-EQUAL）
    # 控制案：零漂移（TEXT-SAME + BYTE-EQUAL）
    # 预存在案：head 与 v145 输出逐字节同=本轮零触碰（排除判定）
    E = {'E1_multi_and_or_nest', 'E2_guard_or_while'}
    PREEXISTING = {'P1_guard_nest', 'P2_flat_and_or', 'P3_guard_multi_or'}
    verdicts = []
    for cid, same, ok in summary:
        if cid in PREEXISTING:
            v = 'PASS' if same else 'FAIL'
            if not same:
                print('verdict %-24s PREEXISTING-DRIFT(head≠v145)=FAIL' % cid)
            else:
                print('verdict %-24s PREEXISTING-PASS(head==v145 零触碰)' % cid)
            verdicts.append(v)
            continue
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-24s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
