# rr-v5r140 [v140-SLCENSUS/CHAINFT/CHAINSTORE] 变体矩阵（A/B 单文件交换：HEAD 623ef8e4 vs v140 工作树）
# 功效案：自环体边界白名单 BUILD_CONST_KEY_MAP + 融合域链式 walrus + 全链输入 walrus
# 控制案：独立 walrus/回边/自环/融合 B234 回归防护
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r140matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v140_%s.py' % k for k in FILES}
os.makedirs(OUT, exist_ok=True)
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：while 体 unpack + 常量键字典 append（BUILD_CONST_KEY_MAP 白名单）
    'E1_while_constkeymap': '''def m1(items):
    res = []
    while items:
        a, b = items.pop()
        res.append({'k': a, 'j': b})
    return res
''',
    # 功效案：融合落空域链式赋值（chain1 形——walrus 误渲染 + b 丢失）
    'E2_ft_chain': '''def k(vs):
    a = b = 0
    for v in vs:
        if v:
            a += v
        else:
            a = b = v
    return a + b
''',
    # 功效案：函数顶全链输入 walrus（chain2 init 形）
    'E3_init_chain': '''def k2(vs):
    a = b = 0
    while vs:
        v = vs.pop()
        if v:
            a += v
        else:
            a = b = v
    return a + b
''',
    # 功效案：融合落空域调用值链式赋值（广度）
    'E4_ft_chain_call': '''def k3(vs, f):
    a = b = None
    for v in vs:
        if v:
            a = v
        else:
            a = b = f(v)
    return a, b
''',
    # 控制案：独立 walrus（COPY+单 STORE+POP_TOP，_cs_n=1 不命中——零漂移）
    'C1_standalone_walrus': '''def w(v):
    (c := v)
    return c + 1
''',
    # 控制案：r137 E1 形（融合域 B234——链检查不抢 B234 归约，回归防护）
    'C2_ft_b234_guard': '''def f(pairs):
    x = y = 0
    hit = []
    for a, b in pairs:
        if a > y:
            y = a
        else:
            hit.append(y)
            x, y = b, a
    return hit, x + y
''',
    # 控制案：r139 E1 形（自环体边界，回归防护）
    'C3_slbody_guard': '''def m(items):
    res = []
    while items:
        a, b = items.pop()
        res.append(a + b)
    return res
''',
    # 控制案：r136 E1 形（回边域，回归防护）
    'C4_backedge_guard': '''def g(blocks):
    i1 = j1 = k1 = 0
    out = []
    for i2, j2, k2 in blocks:
        if i1 + k1 == i2 and j1 + k1 == j2:
            k1 += k2
        else:
            if k1:
                out.append((i1, j1, k1))
            i1, j1, k1 = i2, j2, k2
    return out
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
        v140_py = OUT + '/%s_out_v140.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v140_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v140_py,'rb').read()
        try:
            py_compile.compile(v140_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-24s text_same=%-5s v140_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD walrus 误渲染/丢语句（TEXT-DIFF）→ v140 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    E = {'E1_while_constkeymap', 'E2_ft_chain', 'E3_init_chain', 'E4_ft_chain_call'}
    PREEXISTING = set()
    verdicts = []
    for cid, same, ok in summary:
        if cid in PREEXISTING:
            print('verdict %-24s PREEXISTING-FAIL(非本轮引入，head 同不等)' % cid)
            continue
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-24s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
