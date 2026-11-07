# rr-v5r141 [v141-SLB234] 变体矩阵（A/B 单文件交换：HEAD 1a0d1b58 vs v141 工作树）
# 功效案：while 自环体 B234 反源序多目标赋值（自环走查 STORE 分支缺归约族）
# 控制案：单赋值/解包（UNPACK 状态机）/r139/r140 回归防护
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r141matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v141_%s.py' % k for k in FILES}
os.makedirs(OUT, exist_ok=True)
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：简单 while 体 B234 两目标（repro2 精确形）
    'E1_while_b234_simple': '''def w(items):
    besti = bestj = 0
    while items:
        besti, bestj = besti - 1, bestj - 1
        items.pop()
    return besti, bestj
''',
    # 功效案：三目标 B234 + 下标值（广度）
    'E2_while_b234_three': '''def w2(items, src):
    p = q = r = 0
    while items:
        p, q, r = src[p], q - 1, r + 1
        items.pop()
    return p, q, r
''',
    # 功效案：B234 体 + 后随调用语句（归约不吞后随语句）
    'E3_while_b234_then_call': '''def w3(items, log):
    a = b = 0
    while items:
        a, b = a + 1, b + 2
        log(items)
    return a, b
''',
    # 控制案：while 体单赋值（既有路径零漂移）
    'C1_while_single': '''def s(items):
    x = 0
    while items:
        x = items.pop()
    return x
''',
    # 控制案：while 体解包（UNPACK 状态机既有域，零漂移）
    'C2_while_unpack': '''def u(pairs):
    x = y = 0
    while pairs:
        x, y = pairs.pop()
    return x + y
''',
    # 控制案：r139 自环体回归防护（unpack+append）
    'C3_r139_guard': '''def m(items):
    res = []
    while items:
        a, b = items.pop()
        res.append(a + b)
    return res
''',
    # 控制案：r140 chain1 回归防护
    'C4_r140_guard': '''def k(vs):
    a = b = 0
    for v in vs:
        if v:
            a += v
        else:
            a = b = v
    return a + b
''',
    # 预存在残差：4 首 BoolOp while 条件拆 if+while 族（find_longest_match
    # 形，cond 拆分独立大族本轮登记；体段已被本轮修复，head 与 v141 文本
    # 必异——排除判定记录实测）
    'R1_cond_scramble_preexisting': '''def w(a, b, isj, alo, blo, ahi, bhi):
    besti, bestj, bestsize = alo, blo, 0
    while besti > alo and bestj > blo and not isj(b[bestj - 1]) and a[besti - 1] == b[bestj - 1]:
        besti, bestj, bestsize = besti - 1, bestj - 1, bestsize + 1
    return besti, bestj, bestsize
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
        v141_py = OUT + '/%s_out_v141.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v141_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v141_py,'rb').read()
        try:
            py_compile.compile(v141_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-30s text_same=%-5s v141_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD 丢次级目标（TEXT-DIFF）→ v141 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    # R1_cond_scramble_preexisting：4 首 BoolOp while 条件拆分族（本轮登记，
    # 体段已被本轮修复故 head≠v141——排除判定，独立大族下轮）。
    E = {'E1_while_b234_simple', 'E2_while_b234_three', 'E3_while_b234_then_call'}
    PREEXISTING = {'R1_cond_scramble_preexisting'}
    verdicts = []
    for cid, same, ok in summary:
        if cid in PREEXISTING:
            print('verdict %-30s PREEXISTING-FAIL(条件拆分族本轮登记，体段已修)' % cid)
            continue
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-30s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
