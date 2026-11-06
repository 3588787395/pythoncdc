# rr-v5r127 [v127-TUPKEY] 变体矩阵（A/B 单文件交换：HEAD d796034b vs v127 工作树）
# 功效案：单元素元组下标键（tuple→str 键类型改变 R2 级）
# 控制案：多元素隐式元组（字节等价形）/ 赋值位 1 元组 / 嵌套元组键 / 无元组下标
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r127matrix'
FILES = {'CGN': REPO + '/core/cfg/code_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v127_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    'E1_one_tuple_key': '''def f(d):
    return d[('k',)]
''',
    'E2_one_tuple_key_store': '''def g(d, v):
    d[('k',)] = v
    return d
''',
    'C1_multi_tuple_key': '''def h(d):
    return d[('a', 'b')]
''',
    'C2_assign_one_tuple': '''def i():
    x = ('k',)
    return x
''',
    'C3_nested_tuple_key': '''def j(d):
    return d[(('a',), 'b')]
''',
    'C4_no_tuple_subscript': '''def k(d, key):
    return d[key]
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
        v127_py = OUT + '/%s_out_v127.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v127_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v127_py,'rb').read()
        py_compile.compile(v127_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
        with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
        with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
        ok = byte_equal(orig, prod)
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v127_byte_equal=%s' % (cid, same, ok))
    # E2 实测 HEAD 本已正确（STORE_SUBSCR 位渲染自有 arity 处理，A/B 逐字
    # 节同），归控制；功效案仅 E1（LOAD 位）。
    E = {'E1_one_tuple_key'}
    verdicts = []
    for cid, same, ok in summary:
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
