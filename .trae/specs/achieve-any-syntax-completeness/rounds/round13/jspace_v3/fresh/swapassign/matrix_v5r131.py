# rr-v5r131 [v131-SWAPASSIGN] 变体矩阵（A/B 单文件交换：HEAD b871aea4 vs v131 工作树）
# 功效案：DEREF（cell/闭包）目标 SWAP N 源序元组赋值（B234 守卫②排除域）
# 控制案：FAST/NAME 反源序形（B234 既有域）/UNPACK 形/单目标
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r131matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v131_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：NormalDist.samples 精确形（DEREF + listcomp 闭包 + 前置三元）
    'E1_deref_listcomp_closure': '''import random
class N:
    def samples(self, n):
        gauss = random.gauss if seed is None else random.Random(seed).gauss
        mu, sigma = self._mu, self._sigma
        return [gauss(mu, sigma) for i in range(n)]
''',
    # 功效案：DEREF 双目标普通方法体
    'E2_deref_plain_method': '''class M:
    def m(self):
        mu, sigma = self._mu, self._sigma
        return mu + sigma
''',
    # 功效案：DEREF 三目标（SWAP 3 形）
    'E3_deref_three_targets': '''class T:
    def t(self):
        a, b, c = self.x, self.y, self.z
        return a + b + c
''',
    # 控制案：FAST 反源序形（B234 既有域，零漂移）
    'C1_fast_reverse': '''def f(o):
    a, b = o.x, o.y
    return a + b
''',
    # 控制案：FAST 三目标反源序
    'C2_fast_three': '''def g(o):
    c, d, e = o.x, o.y, o.z
    return c + d + e
''',
    # 控制案：单目标 DEREF（无连续段）
    'C3_single_deref': '''class S:
    def s(self):
        mu = self._mu
        return mu
''',
    # 控制案：常量元组 UNPACK 形（既有 UNPACK 分支）
    'C4_unpack_const': '''def u():
    a, b = 1, 2
    return a + b
''',
    # 控制案：DEREF 目标但有 UNPACK（闭包解包非 SWAP 形）
    'C5_deref_unpack': '''class W:
    def w(self, pair):
        a, b = pair
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
        v131_py = OUT + '/%s_out_v131.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v131_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v131_py,'rb').read()
        try:
            py_compile.compile(v131_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v131_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD 丢目标（TEXT-DIFF）→ v131 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    # E2/E3 实测 HEAD 本已等价（普通方法体走主 walk SIG2 的 R68-b2 cell-swap
    # 分支）——归控制零漂移证据；功效案仅 E1（三元邻接形走
    # _build_statements_from_instructions，彼 walk 无 R68-b2 对应分支）。
    E = {'E1_deref_listcomp_closure'}
    verdicts = []
    for cid, same, ok in summary:
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
