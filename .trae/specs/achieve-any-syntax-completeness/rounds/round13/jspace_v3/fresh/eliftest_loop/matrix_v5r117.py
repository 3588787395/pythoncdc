# rr-v5r117 [v117-ELIFTEST] 变体矩阵（A/B 文件交换：HEAD 2292a8c2 vs v117 工作树）
# 功效案：while 复合条件 + 体内 if/elif 链且臂测试 load ⊆ 循环条件变量集
#   （HEAD 误吸臂测试块为闩锁重检块 → elif 测试消失、臂折叠进 else）
# 控制案：无链复合 while / 非条件变量 if / 经典增量 while / 首臂 if 形
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r117matrix'
GEN = REPO + '/core/cfg/region_ast_generator.py'
V117_COPY = OUT + '/region_ast_generator_v117.py'
PY = 'D:/Python/python.exe'
shutil.copy(GEN, V117_COPY)

CASES = {
    # ---- 功效案 ----
    # E1: REAL46-019 address_exclude 精确形（生成器 while 内三臂链，elif 测试
    #     load {other, s2} ⊆ 条件变量 {s1, s2, other}）
    'E1_eliftest_gen': '''class _BaseNetwork:
    def _version(self):
        return 4

    def address_exclude(self, other):
        """exclude"""
        if not self._version == other._version:
            raise TypeError("%s and %s are not of the same version" % (
                             self, other))

        if not isinstance(other, _BaseNetwork):
            raise TypeError("%s is not a network object" % other)

        if not other.subnet_of(self):
            raise ValueError('%s not contained in %s' % (other, self))
        if other == self:
            return

        other = other.__class__('%s/%s' % (other.network_address,
                                           other.prefixlen))

        s1, s2 = self.subnets()
        while s1 != other and s2 != other:
            if other.subnet_of(s1):
                yield s2
                s1, s2 = s1.subnets()
            elif other.subnet_of(s2):
                yield s1
                s1, s2 = s2.subnets()
            else:
                raise AssertionError('Error performing exclusion: '
                                     's1: %s s2: %s other: %s' %
                                     (s1, s2, other))
        if s1 == other:
            yield s2
        elif s2 == other:
            yield s1
        else:
            raise AssertionError('Should not have gotten here')
''',
    # E2: 非生成器同构（方法版三臂链）
    'E2_eliftest_nongen': '''class N:
    def ex(self, other):
        s1, s2 = self.subnets()
        while s1 != other and s2 != other:
            if other.subnet_of(s1):
                self.out.append(s2)
                s1, s2 = s1.subnets()
            elif other.subnet_of(s2):
                self.out.append(s1)
                s1, s2 = s2.subnets()
            else:
                raise AssertionError('nope')
        if s1 == other:
            self.out.append(s2)
        elif s2 == other:
            self.out.append(s1)
        else:
            raise AssertionError('nope2')
''',
    # E3: if/elif 双臂（首臂为 entry、elif 为非 entry，同 repro2 机制面）
    'E3_eliftest_twoarm': '''def m4(a, b):
    while a != b and b > 0:
        if a > b:
            a -= 1
        elif b > 2:
            b -= 2
    return a
''',
    # ---- 控制案 ----
    # C1: 复合条件 while、体无 if 链（吸收域无 Region 入口块，零漂移）
    'C1_while_compound_plain': '''def f(data, n):
    out = []
    while n > 0 and len(out) < n:
        out.append(data)
        n -= 1
    return out
''',
    # C2: 体内 if 测试 load 非条件变量（两侧都不吸收，零漂移）
    'C2_if_noncondvar': '''def g(a, b, flag):
    while a != b and b > 0:
        if flag:
            a += 1
        else:
            b -= 1
    return a
''',
    # C3: 经典增量 while（回边无条件跳转，不进候选域）
    'C3_while_incr': '''def k(data):
    i = 0
    while i < len(data):
        i += 1
    return i
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

if __name__ == '__main__':
    head_export = OUT + '/region_ast_generator_head.py'
    r = subprocess.run(['git', '-C', REPO, 'show', 'HEAD:core/cfg/region_ast_generator.py'], capture_output=True)
    open(head_export, 'wb').write(r.stdout)

    summary = []
    for cid in CASES:
        head_py = OUT + '/%s_out_head.py' % cid
        v117_py = OUT + '/%s_out_v117.py' % cid
        shutil.copy(head_export, GEN)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        shutil.copy(V117_COPY, GEN)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v117_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v117_py,'rb').read()
        py_compile.compile(v117_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
        with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
        with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
        ok = byte_equal(orig, prod)
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v117_byte_equal=%s' % (cid, same, ok))

    E = {'E1_eliftest_gen', 'E2_eliftest_nongen', 'E3_eliftest_twoarm'}
    verdicts = []
    for cid, same, ok in summary:
        if cid in E:
            v = 'PASS' if ((not same) and ok) else 'FAIL'
        else:
            v = 'PASS' if (same and ok) else 'FAIL'
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
