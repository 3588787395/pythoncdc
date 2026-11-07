# rr-v5r139 [v139-SLBODYEXPR] 变体矩阵（A/B 单文件交换：HEAD 39a4d2ff vs v139 工作树）
# 功效案：while 自循环体边界扩展白名单补纯表达式操作码（尾语句带表达式实参被截断族）
# 控制案：无 STORE 体（全长路径）/单 STORE 体/多 POP_TOP 栈模拟路径/算术条件重检/回归防护
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r139matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v139_%s.py' % k for k in FILES}
os.makedirs(OUT, exist_ok=True)
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：while 体 unpack + append(a + b)（C4_body_tuple 精确形）
    'E1_while_unpack_append': '''def m(items):
    res = []
    while items:
        a, b = items.pop()
        res.append(a + b)
    return res
''',
    # 功效案：while 体 unpack + append(a + 1)（LOAD_CONST 白名单补齐）
    'E2_while_unpack_const': '''def m2(items):
    res = []
    while items:
        a, b = items.pop()
        res.append(a + 1)
    return res
''',
    # 功效案：while 体 unpack + append(b[0])（BINARY_SUBSCR 白名单补齐）
    'E3_while_unpack_subscr': '''def m3(items, lookup):
    res = []
    while items:
        a, b = items.pop()
        res.append(lookup[b])
    return res
''',
    # 控制案：while 体无 STORE 调用（全长路径零漂移）
    'C1_while_nostore': '''def f2(x):
    while x:
        print(x)
    return 0
''',
    # 控制案：while 体单 STORE（既有边界零漂移）
    'C2_while_single_store': '''def s(items):
    x = 0
    while items:
        x = items.pop()
    return x
''',
    # 控制案：while 体两条调用（多 POP_TOP 栈模拟路径零漂移）
    'C3_while_two_calls': '''def t(items, log):
    while items:
        log(items.pop())
        print(items)
    return 0
''',
    # 控制案：算术条件重检（重检求值段边界不变，零漂移）
    'C4_while_arith_cond': '''def w(a, y):
    while a + 1 > y:
        a = a - 1
    return a
''',
    # 控制案：r138 E1 形（融合落空域）回归防护
    'C5_r138_guard': '''def m(pairs):
    x = y = 0
    for p in pairs:
        if x:
            x -= 1
        else:
            x, y = p
    return x + y
''',
    # 控制案：r136 E1 形（回边域）回归防护
    'C6_r136_guard': '''def g(blocks):
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
        v139_py = OUT + '/%s_out_v139.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v139_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v139_py,'rb').read()
        try:
            py_compile.compile(v139_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v139_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD 丢尾语句（TEXT-DIFF）→ v139 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    E = {'E1_while_unpack_append', 'E2_while_unpack_const', 'E3_while_unpack_subscr'}
    PREEXISTING = set()
    verdicts = []
    for cid, same, ok in summary:
        if cid in PREEXISTING:
            print('verdict %-26s PREEXISTING-FAIL(非本轮引入，head 同不等)' % cid)
            continue
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
