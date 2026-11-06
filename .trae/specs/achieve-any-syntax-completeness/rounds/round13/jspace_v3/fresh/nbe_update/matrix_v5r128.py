# rr-v5r128 [v128-NBEUPD] 变体矩阵（A/B 单文件交换：HEAD 23c0b6b7 vs v128 工作树）
# 功效案：NONE_CHECK 旋转 while 环底更新语句丢失族（真实 R1：循环不前进）
# 控制案：walrus 对（B105）/ COMPARE_OP 族（n-=1）/ truthy 族 / 多语句环底更新
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r128matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v128_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    'E1_e2_shape': '''def w(toks, ns, pa):
    it = iter(toks)
    tok = next(it, None)
    while tok is not None:
        if tok == 'a':
            yield ('a', tok)
        elif ns and not pa:
            yield ('n', ns)
        else:
            yield tok
        tok = next(it, None)
''',
    'E2_is_none_variant': '''def f(it):
    tok = next(it, None)
    out = []
    while tok is None:
        out.append(tok)
        tok = next(it, None)
    return out
''',
    'E4_multi_stmt_update': '''def g(it, acc):
    tok = next(it, None)
    count = 0
    while tok is not None:
        acc.append(tok)
        tok = next(it, None)
        count += 1
    return count
''',
    'E3_walrus_control': '''def h(it):
    out = []
    while (m := next(it, None)) is not None:
        out.append(m)
    return out
''',
    'C1_if_false_control': '''def k(n):
    total = 0
    while n > 0:
        total += n % 3
        n -= 1
    return total
''',
    'C2_truthy_control': '''def m(it):
    out = []
    tok = next(it, None)
    while tok:
        out.append(tok)
        tok = next(it, None)
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
        v128_py = OUT + '/%s_out_v128.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v128_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v128_py,'rb').read()
        try:
            py_compile.compile(v128_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v128_byte_equal=%s' % (cid, same, ok))
    # 功效案：E1（HEAD 丢更新 TEXT-DIFF → v128 BYTE-EQUAL）。
    # E2/E4 实测 HEAD 本已正确（兄弟形态走其他提取路径，text_same=True
    # 且 v128 byte_equal ⇒ HEAD 亦 byte_equal）——归控制案零漂移证据。
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    E = {'E1_e2_shape'}
    verdicts = []
    for cid, same, ok in summary:
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
