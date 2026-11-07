# rr-v5r146 [v146-ORFLAT] 变体矩阵（A/B 单文件交换：HEAD 7c92b061 vs v146 工作树）
# 功效案：扁平 and-or while 条件（and 组被守卫 if 外提族）
# 控制案：嵌套链/守卫 or/and 链/自环 回归防护
# 预存在案：守卫嵌套/or+and 尾（head==v146 逐字节同，登记）
import os, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r146matrix'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    # 功效案 1：F1 扁平 and-or（含 init 前导 STORE 于链首块）
    'E1_flat_and_or': '''def h(a, b, c):
    i = 0
    while i < 5 and b[i] or c[i]:
        i += 1
    return i
''',
    # 功效案 2：F2 扁平 and-or 纯名操作数
    'E2_flat_names': '''def h(a, b, c):
    while a and b or c:
        a -= 1
    return a
''',
    # 控制案：na5（v144 嵌套形，扁平判据不得误触发）
    'C1_na5': '''def f(items, opt):
    i = 0
    while i < len(items) and (items[i] or opt):
        i += 1
    return i
''',
    # 控制案：D1 守卫 + 纯 or while（v145 回归修复维持）
    'C2_guard_or': '''def f(a, b, c):
    if a:
        while b or c:
            b -= 1
    return a
''',
    # 控制案：r145 E1 多块 and 头嵌套（维持）
    'C3_multi_nest': '''def g(a, b, c, f):
    i = 1
    while i < 10 and a[i] and (b[i] or f(i)):
        i += 1
    return i
''',
    # 控制案：r143 纯 or 链
    'C4_or2': '''def c2(a, b):
    i = 0
    while i > 3 or b[i] == 1:
        i += 1
    return i
''',
    # 控制案：r142 4 首 and 链
    'C5_and4': '''def w(a, b, isj, alo, blo, ahi, bhi):
    besti, bestj, bestsize = alo, blo, 0
    while besti > alo and bestj > blo and not isj(b[bestj - 1]) and a[besti - 1] == b[bestj - 1]:
        besti, bestj, bestsize = besti - 1, bestj - 1, bestsize + 1
    return besti, bestj, bestsize
''',
    # 控制案：r141 自环 B234
    'C6_r141': '''def w(items):
    besti = bestj = 0
    while items:
        besti, bestj = besti - 1, bestj - 1
        items.pop()
    return besti, bestj
''',
    # 控制案：r139 自环体
    'C7_r139': '''def m(items):
    res = []
    while items:
        a, b = items.pop()
        res.append(a + b)
    return res
''',
    # 预存在案：G1 守卫 + 嵌套 and+(or)（守卫外提族，登记）
    'P1_guard_nest': '''def f(a, b, c, d):
    if a:
        while b and (c or d):
            b -= 1
    return a
''',
    # 预存在案：F3 or + and 尾（or_groups 分组族，登记）
    'P2_or_and_tail': '''def h(a, b, c):
    i = 0
    while i > 3 or b[i] and c[i]:
        i += 1
    return i
''',
    # 预存在案：D3 守卫 + 嵌套（登记）
    'P3_guard_nest2': '''def f(a, b, c, d):
    if a and b:
        while c or d:
            b -= 1
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
    FILES = {'RA': REPO + '/core/cfg/region_analyzer.py'}
    for k, p in FILES.items():
        shutil.copy(p, OUT + '/v146_%s.py' % k)
    head_exports = {}
    for k, p in FILES.items():
        r = subprocess.run(['git', '-C', REPO, 'show', '7c92b061:' + p.replace(REPO + '/', '')], capture_output=True)
        hp = OUT + '/head_%s.py' % k
        open(hp, 'wb').write(r.stdout)
        head_exports[k] = hp
    summary = []
    for cid in CASES:
        head_py = OUT + '/%s_out_head.py' % cid
        v146_py = OUT + '/%s_out_v146.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(OUT + '/v146_%s.py' % k, p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v146_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v146_py,'rb').read()
        try:
            py_compile.compile(v146_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-22s text_same=%-5s v146_byte_equal=%s' % (cid, same, ok))
    E = {'E1_flat_and_or', 'E2_flat_names'}
    PREEXISTING = {'P1_guard_nest', 'P2_or_and_tail', 'P3_guard_nest2'}
    verdicts = []
    for cid, same, ok in summary:
        if cid in PREEXISTING:
            v = 'PASS' if same else 'FAIL'
            print('verdict %-22s %s' % (cid, 'PREEXISTING-PASS(head==v146 零触碰)' if same else 'PREEXISTING-DRIFT=FAIL'))
            verdicts.append(v)
            continue
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-22s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
