# rr-v5r132 [v132-CHAINESELSE] 变体矩阵（A/B 单文件交换：HEAD 1e24ff69 vs v132 工作树）
# 功效案：elif 链末臂非终态 + else 体（分析端 merge 误判压平域）
# 控制案：终态臂链/真汇合 if-else/无 else 链（既有域零漂移）
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r132matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v132_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：harmonic_mean 精确形（末臂非终态 + else 含嵌套 if×2 + 尾语句）
    'E1_chain_else_flatten': '''def hm(data, weights, n):
    if n < 1:
        raise ValueError('a')
    elif n == 1 and weights is None:
        x = data[0]
        return x
    if weights is None:
        w = 1
        s = n
    else:
        if weights:
            weights = list(weights)
        if len(weights) != n:
            raise ValueError('c')
        s = 2
    return s
''',
    # 功效案：末臂非终态 + else 单嵌套 if
    'E2_chain_else_single_if': '''def f(v, lim):
    if v < 0:
        return -1
    elif v == 0:
        return 0
    if v > lim:
        tag = 'h'
    else:
        if v % 2:
            tag = 'odd'
        tag = tag + '!'
    return tag
''',
    # 控制案：终态臂 if/elif/else 链（Round 8 既有域）
    'C1_terminal_chain': '''def g(a):
    if a > 10:
        return 1
    elif a > 5:
        return 2
    else:
        return 3
''',
    # 控制案：if/elif 无 else（链后尾随语句——不得吸收）
    'C2_chain_no_else': '''def h(a, b):
    if a > 10:
        r = 1
    elif a > 5:
        r = 2
    return r + b
''',
    # 控制案：双臂非终态 if-else（真汇合 merge——恢复判据不得命中）
    'C3_true_merge_ifelse': '''def k(v):
    if v:
        x = v + 1
    else:
        x = 2
    return x
''',
    # 控制案：if-elif 链 + else 且末臂终态（既有 final_else 通道）
    'C4_terminal_last_else': '''def m(a, flag):
    if a > 10:
        r = 1
    elif a > 5:
        return 2
    else:
        if flag:
            r = 3
        r = r + 1
    return r
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
        v132_py = OUT + '/%s_out_v132.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v132_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v132_py,'rb').read()
        try:
            py_compile.compile(v132_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v132_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD 压平（TEXT-DIFF）→ v132 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    # E2 实测 HEAD 本已等价（单嵌套 if 形结构不同不触发 merge 误判）——
    # 归控制零漂移证据；功效案仅 E1（harmonic_mean 精确形）。
    E = {'E1_chain_else_flatten'}
    verdicts = []
    for cid, same, ok in summary:
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
