# rr-v5r134 [v134-LOOPB234] 变体矩阵（A/B 单文件交换：HEAD f190d0ef vs v134 工作树）
# 功效案：while 前缀提取器 B234 反源序多目标赋值（丢首目标=真实 R1）
# 控制案：单赋值/非循环前缀（B234 主 walk 域）/三目标/skip 交互
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r134matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v134_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：while 前缀元组赋值（get_matching_blocks 精确形）
    'E1_loop_prefix_tuple': '''def g(a, b):
    la, lb = len(a), len(b)
    queue = [(0, la, 0, lb)]
    out = []
    while queue:
        x = queue.pop()
        out.append(x)
    return out, la + lb
''',
    # 功效案：while 前缀方法调用值元组赋值
    'E2_loop_prefix_method_tuple': '''class S:
    def m(self):
        la, lb = len(self.a), len(self.b)
        q = [(la, lb)]
        while q:
            q.pop()
        return la + lb
''',
    # 控制案：while 前缀单赋值（既有路径零漂移）
    'C1_loop_prefix_single': '''def f(a, b):
    n = len(a)
    out = []
    while b:
        out.append(b.pop())
    return out, n
''',
    # 控制案：非循环上下文元组赋值（B234 主 walk 域）
    'C2_no_loop_tuple': '''def h(a, b):
    x, y = len(a), len(b)
    return x + y
''',
    # 控制案：三目标 while 前缀元组赋值
    'C3_three_targets': '''def k(a, b, c):
    p, q, r = len(a), len(b), len(c)
    acc = [p, q, r]
    while acc:
        acc.pop()
    return p + q + r
''',
    # 控制案：循环体元组赋值（非前缀）
    'C4_body_tuple': '''def m(items):
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
        v134_py = OUT + '/%s_out_v134.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v134_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v134_py,'rb').read()
        try:
            py_compile.compile(v134_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v134_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD 丢首目标（TEXT-DIFF）→ v134 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    # C3 实测同为功效案（三目标 HEAD 亦丢目标，v134 修复 BYTE-EQUAL）。
    # C4 实测预存在残差（text_same=True⇒HEAD 同产品同不等——循环体
    # UNPACK 元组族，本轮未触碰，登记下轮候选），排除判定。
    E = {'E1_loop_prefix_tuple', 'E2_loop_prefix_method_tuple',
         'C3_three_targets'}
    PREEXISTING = {'C4_body_tuple'}
    verdicts = []
    for cid, same, ok in summary:
        if cid in PREEXISTING:
            print('verdict %-26s PREEXISTING-FAIL(非本轮引入)' % cid)
            continue
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
