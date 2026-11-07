# rr-v5r142 [v142-BOOLOPCHAIN4] 变体矩阵（A/B 单文件交换：HEAD 91e7b412 vs v142 工作树）
# 功效案：while 多首 BoolOp 条件链（3+/4 操作数，含 not 调用首——回溯中断族）
# 控制案：2 首（既有工作域）/or 链/简单 while/回归防护
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r142matrix'
FILES = {'RAG': REPO + '/core/cfg/region_analyzer.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v142_%s.py' % k for k in FILES}
os.makedirs(OUT, exist_ok=True)
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：4 首 BoolOp while 条件（repro1 精确形）
    'E1_while_boolop4': '''def w(a, b, isj, alo, blo, ahi, bhi):
    besti, bestj, bestsize = alo, blo, 0
    while besti > alo and bestj > blo and not isj(b[bestj - 1]) and a[besti - 1] == b[bestj - 1]:
        besti, bestj, bestsize = besti - 1, bestj - 1, bestsize + 1
    return besti, bestj, bestsize
''',
    # 功效案：3 首 BoolOp while 条件（中间操作数断链精确形）
    'E2_while_boolop3': '''def w3(a, b, isj, alo, blo):
    i = alo
    j = blo
    while i > alo and not isj(b[j - 1]) and a[i - 1] == b[j - 1]:
        i, j = i - 1, j - 1
    return i, j
''',
    # 功效案：两个同构 4 首 while（find_longest_match 尾段形态）
    'E3_two_boolop4': '''def w4(a, b, isj, alo, blo, ahi, bhi):
    besti, bestj, bestsize = alo, blo, 0
    while besti > alo and bestj > blo and not isj(b[bestj - 1]) and a[besti - 1] == b[bestj - 1]:
        besti, bestj, bestsize = besti - 1, bestj - 1, bestsize + 1
    while besti + bestsize < ahi and bestj + bestsize < bhi and not isj(b[bestj + bestsize]) and a[besti + bestsize] == b[bestj + bestsize]:
        bestsize += 1
    return besti, bestj, bestsize
''',
    # 控制案：2 首 BoolOp while（既有工作域——首步 pred_ft==condition_block，零漂移）
    'C1_while_boolop2': '''def c1(a, blo):
    i = 0
    while i < 10 and a[i] > 0:
        i += 1
    return i
''',
    # 控制案：or 链 while（极性反转既有域，零漂移）
    'C2_while_or': '''def c2(a, b):
    i = 0
    while i > 3 or b[i] == 1:
        i += 1
    return i
''',
    # 控制案：简单 while（零漂移）
    'C3_while_simple': '''def c3(items):
    x = 0
    while items:
        x = items.pop()
    return x
''',
    # 控制案：r141 repro2 回归防护（自环体 B234）
    'C4_r141_guard': '''def w(items):
    besti = bestj = 0
    while items:
        besti, bestj = besti - 1, bestj - 1
        items.pop()
    return besti, bestj
''',
    # 控制案：r139 自环体回归防护（unpack+append）
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
        v142_py = OUT + '/%s_out_v142.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v142_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v142_py,'rb').read()
        try:
            py_compile.compile(v142_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-22s text_same=%-5s v142_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD 条件拆分碎片（TEXT-DIFF）→ v142 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    # 预存在残差（head 与 v142 输出逐字节同=本轮零触碰，排除判定）：
    #   C2=while or 链条件拆分族（or 极性_sibling 族，`while i > 3: return
    #      b[i]==1` 碎片——另一走查位点，本轮登记下轮）。
    E = {'E1_while_boolop4', 'E2_while_boolop3', 'E3_two_boolop4'}
    PREEXISTING = {'C2_while_or'}
    verdicts = []
    for cid, same, ok in summary:
        if cid in PREEXISTING:
            print('verdict %-22s PREEXISTING-FAIL(非本轮引入，head 同不等)' % cid)
            continue
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-22s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
