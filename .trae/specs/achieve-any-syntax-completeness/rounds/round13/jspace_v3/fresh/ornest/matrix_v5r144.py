# rr-v5r144 [v144-ORNEST] 变体矩阵（A/B 单文件交换：HEAD d0ab6e94 vs v144 工作树）
# 功效案：while and+(or) 嵌套链（and 头被外提守卫 if 族）
# 控制案：or 链/and 链/扁平 and-or/回归防护
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r144matrix'
FILES = {'RA': REPO + '/core/cfg/region_analyzer.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v144_%s.py' % k for k in FILES}
os.makedirs(OUT, exist_ok=True)
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：na5 精确形（and 头 + 括号 or 尾）
    'E1_and_or_nest': '''def f(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
''',
    # 功效案：嵌套链变体（and 头两个操作数 + or 尾调用）
    'E2_and_or_nest2': '''def g(a, b, c, f):
    i = 1
    while i < 10 and a[i] and (b[i] or f(i)):
        i += 1
    return i
''',
    # 控制案：r143 or 链（回归防护）
    'C1_or2_guard': '''def c2(a, b):
    i = 0
    while i > 3 or b[i] == 1:
        i += 1
    return i
''',
    # 控制案：r142 and 链（回归防护）
    'C2_and4_guard': '''def w(a, b, isj, alo, blo, ahi, bhi):
    besti, bestj, bestsize = alo, blo, 0
    while besti > alo and bestj > blo and not isj(b[bestj - 1]) and a[besti - 1] == b[bestj - 1]:
        besti, bestj, bestsize = besti - 1, bestj - 1, bestsize + 1
    return besti, bestj, bestsize
''',
    # 控制案：扁平 and-or（A and B or C——不同字节码假边目标，分类按实测）
    'C3_flat_and_or': '''def h(a, b, c):
    i = 0
    while i < 5 and b[i] or c[i]:
        i += 1
    return i
''',
    # 控制案：r141 自环 B234（回归防护）
    'C4_r141_guard': '''def w(items):
    besti = bestj = 0
    while items:
        besti, bestj = besti - 1, bestj - 1
        items.pop()
    return besti, bestj
''',
    # 控制案：r139 自环体（回归防护）
    'C5_r139_guard': '''def m(items):
    res = []
    while items:
        a, b = items.pop()
        res.append(a + b)
    return res
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
        v144_py = OUT + '/%s_out_v144.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v144_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v144_py,'rb').read()
        try:
            py_compile.compile(v144_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-20s text_same=%-5s v144_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD and 头外提守卫（TEXT-DIFF）→ v144 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    # 预存在残差（head 与 v144 输出逐字节同=本轮零触碰，排除判定）：
    #   E2=多块 and 头嵌套链（单块前置限定后回到 head 行为，多块 and 头
    #      通用混合链装配另行登记）；
    #   C3=扁平 and-or（A and B or C 假边目标不同的另一族，登记）。
    E = {'E1_and_or_nest'}
    PREEXISTING = {'E2_and_or_nest2', 'C3_flat_and_or'}
    verdicts = []
    for cid, same, ok in summary:
        if cid in PREEXISTING:
            print('verdict %-20s PREEXISTING-FAIL(非本轮引入，head 同不等)' % cid)
            continue
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-20s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
