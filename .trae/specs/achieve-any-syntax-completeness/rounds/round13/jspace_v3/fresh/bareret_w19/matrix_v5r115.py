# rr-v5r115 [v115-BARERET] 变体矩阵（A/B 文件交换：HEAD 5e16ae25 vs v115 工作树）
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r115matrix'
GEN = REPO + '/core/cfg/region_ast_generator.py'
V115_COPY = OUT + '/region_ast_generator_v115.py'
PY = 'D:/Python/python.exe'
shutil.copy(GEN, V115_COPY)

CASES = {
    # ---- 功效案 ----
    'E1_bare_ret_tail': '''class W:
    def m(self, state):
        self._log = []
        if isinstance(state, tuple):
            if len(state) == 6:
                self._p, self._q = state[:2]
                return
            if len(state) == 2:
                _, slot = state
                self._x = slot
        self._tail = 1
        return ("tail", getattr(self, "_x", None))
''',
    'E2_bare_ret_nested': '''class V:
    def __setstate__(self, state):
        self._a = None
        self._b = None
        if isinstance(state, tuple):
            if len(state) == 6:
                self._p, self._q = state
                return
            if len(state) == 2:
                _, slot_dict = state
                if isinstance(slot_dict, dict):
                    self._x = slot_dict["_x"]
                    self._y = slot_dict["_y"]
                    return
        if isinstance(state, dict):
            version_nt = state.get("_v")
            if version_nt is not None:
                self._z = version_nt
''',
    # ---- 控制案 ----
    'C1_epilogue_unpack': '''def load(conn):
    a, b = conn.get()
    return a + b
''',
    'C1b_epilogue_only': '''def f(g):
    a, b = g()
''',
    'C2_bare_ret_last': '''def f(g, x):
    a, b = g()
    if x:
        c, d = g()
        return
    return a + b
''',
    'C3_valret_arm': '''class W:
    def m(self, state):
        self._log = []
        if isinstance(state, tuple):
            if len(state) == 6:
                self._p, self._q = state[:2]
                return ("six", self._p, self._q)
            if len(state) == 2:
                _, slot = state
                self._x = slot
        self._tail = 1
        return ("tail", getattr(self, "_x", None))
''',
    'C4_attr_unpack': '''def h(f):
    a, self_conn.b = f()
    return a
''',
    'C5_quot_shape': '''def q(f):
    x, y = f()
    return x, y
''',
    'C6_unpack_mid': '''def m2(g):
    a, b = g()
    print(a, b)
    return b
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
    
    head_export = OUT + '/region_ast_generator_head.py'
    r = subprocess.run(['git', '-C', REPO, 'show', 'HEAD:core/cfg/region_ast_generator.py'], capture_output=True)
    open(head_export, 'wb').write(r.stdout)
    
    summary = []
    for cid in CASES:
        head_py = OUT + '/%s_out_head.py' % cid
        v115_py = OUT + '/%s_out_v115.py' % cid
        shutil.copy(head_export, GEN)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        shutil.copy(V115_COPY, GEN)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v115_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v115_py,'rb').read()
        py_compile.compile(v115_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
        with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
        with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
        ok = byte_equal(orig, prod)
        summary.append((cid, same, ok))
        print('%-22s text_same=%-5s v115_byte_equal=%s' % (cid, same, ok))
    
    E = {'E1_bare_ret_tail', 'E2_bare_ret_nested', 'C2_bare_ret_last'}  # C2: if 臂内裸 return（非尾声块）实测同为功效案
    verdicts = []
    for cid, same, ok in summary:
        if cid in E:
            v = 'PASS' if ((not same) and ok) else 'FAIL'
        else:
            v = 'PASS' if (same and ok) else 'FAIL'
        verdicts.append(v)
        print('verdict %-22s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
