# rr-v5r135 [v135-CHAINUNPACK] 变体矩阵（A/B 单文件交换：HEAD 400540a8 vs v135 工作树）
# 功效案：链式元组解包（i, j, k = x = value 形——COPY 1 + UNPACK + 链尾 STORE）
# 控制案：普通解包/简单链（B85 域）/无循环上下文
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r135matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v135_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：while 体链式元组解包（get_matching_blocks 精确形）
    'E1_chain_unpack_while': '''def g(items, out):
    while items:
        i, j, k = x = items.pop()
        if k:
            out.append(x)
    return out
''',
    # 功效案：if 体链式元组解包（同提取器无循环上下文）
    'E2_chain_unpack_if': '''def f(items):
    if items:
        a, b = y = items.pop()
        return a + b + (y is not None)
    return 0
''',
    # 控制案：普通元组解包（既有 UNPACK 分支零漂移）
    'C1_plain_unpack': '''def h(items):
    while items:
        a, b = items.pop()
        if a:
            return b
    return 0
''',
    # 控制案：简单名链 a = b = v（B85 既有域）
    'C2_simple_chain': '''def k(v):
    a = b = v
    return a + b
''',
    # 控制案：函数顶链式元组解包（非 if/while 条件块前导段）
    'C3_top_chain_unpack': '''def m(items):
    a, b = y = items.pop()
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
        v135_py = OUT + '/%s_out_v135.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v135_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v135_py,'rb').read()
        try:
            py_compile.compile(v135_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-24s text_same=%-5s v135_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD 丢链尾目标（TEXT-DIFF）→ v135 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    # E2 实测 HEAD 本已等价（if 体形走其他路径）——归控制；功效案仅 E1
    # （while 体形，get_matching_blocks 精确域）。
    E = {'E1_chain_unpack_while'}
    verdicts = []
    for cid, same, ok in summary:
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-24s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
