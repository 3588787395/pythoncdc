# rr-v5r143 [v143-ORCHAIN] 变体矩阵（A/B 双文件交换：HEAD 13610dcc vs v143 工作树）
# 功效案：while or 链条件拆分族（or 链前向闭合 + 链首前缀保留）
# 控制案：and 链/非循环 or/r139-r142 回归防护
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r143matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py',
         'RA': REPO + '/core/cfg/region_analyzer.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v143_%s.py' % k for k in FILES}
os.makedirs(OUT, exist_ok=True)
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：2 首 or 链 while（r142 矩阵 C2 精确形——junk return + init 丢失）
    'E1_while_or2': '''def c2(a, b):
    i = 0
    while i > 3 or b[i] == 1:
        i += 1
    return i
''',
    # 功效案：3 首 or 链 while（or 尾 run 广度）
    'E2_while_or3': '''def c3(a, b, c):
    i = 0
    while i > 3 or b[i] == 1 or c[i]:
        i += 1
    return i
''',
    # 功效案：or 链第二操作数带调用（前向续接域）
    'E3_while_or_call': '''def c4(a, b, f):
    n = 0
    while n > 2 or f(b[n]):
        n += 1
    return n
''',
    # 控制案：and 链 while（r142 功效域回归防护）
    'C1_and_chain_guard': '''def w(a, b, isj, alo, blo, ahi, bhi):
    besti, bestj, bestsize = alo, blo, 0
    while besti > alo and bestj > blo and not isj(b[bestj - 1]) and a[besti - 1] == b[bestj - 1]:
        besti, bestj, bestsize = besti - 1, bestj - 1, bestsize + 1
    return besti, bestj, bestsize
''',
    # 控制案：非循环 or 链 if（不同域，零漂移）
    'C2_if_or': '''def g(a, b):
    if a > 3 or b[0] == 1:
        return 1
    return 0
''',
    # 控制案：r141 自环体回归防护（B234）
    'C3_r141_guard': '''def w(items):
    besti = bestj = 0
    while items:
        besti, bestj = besti - 1, bestj - 1
        items.pop()
    return besti, bestj
''',
    # 控制案：r139 自环体回归防护（unpack+append）
    'C4_r139_guard': '''def m(items):
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
        v143_py = OUT + '/%s_out_v143.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v143_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v143_py,'rb').read()
        try:
            py_compile.compile(v143_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-20s text_same=%-5s v143_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD or 条件拆分碎片（TEXT-DIFF）→ v143 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    E = {'E1_while_or2', 'E2_while_or3', 'E3_while_or_call'}
    PREEXISTING = set()
    verdicts = []
    for cid, same, ok in summary:
        if cid in PREEXISTING:
            print('verdict %-20s PREEXISTING-FAIL(非本轮引入，head 同不等)' % cid)
            continue
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-20s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
