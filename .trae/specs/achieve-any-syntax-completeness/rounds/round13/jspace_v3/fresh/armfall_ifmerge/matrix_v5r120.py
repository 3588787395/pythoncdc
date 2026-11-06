# rr-v5r120 [v120-ARMFALL] 变体矩阵（A/B 四文件交换：HEAD 4baf2261 vs v120 工作树）
# 功效案：while 1 + 体内 if 破/续 + 独立 if（quote 调整臂直落）+ 无条件后随语句
#   ——HEAD 把后随语句折进直落臂的假边专属 else（quote 臂成立时丢失执行，
#   真实 R1）；v120 臂直落标记 + 转换器/代码生成否证折入
# 控制案：v119 全部矩阵案（TRYTOP 域零漂移）+ 真 else 链 + 无循环直落臂
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r120matrix'
FILES = {
    'ANA': REPO + '/core/cfg/region_analyzer.py',
    'RAG': REPO + '/core/cfg/region_ast_generator.py',
    'ACV': REPO + '/core/cfg/ast_converter.py',
    'CGN': REPO + '/core/cfg/code_generator.py',
}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v120_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # ---- 功效案 ----
    'E1_armfall_quote': '''def p2(next, token, signature, predicate):
    while 1:
        try:
            token = next()
        except StopIteration:
            return
        if token[0] == ']':
            break
        if token == ('', ''):
            continue
        if token[0] and token[0][:1] in "'":
            token = ("'", token[0][1:-1])
        signature.append(token[0] or '-')
        predicate.append(token[1])
    return ''.join(signature)
''',
    'E2_armfall_assign': '''def q(next, token, out):
    while 1:
        try:
            token = next()
        except StopIteration:
            return
        if token == 'end':
            break
        if token == '':
            continue
        if token.startswith('@'):
            out['k'] = token
        out['v'] = token
    return out
''',
    # ---- 控制案 ----
    'C1_trytop_while1': '''def p(next, token, signature):
    while 1:
        try:
            token = next()
        except StopIteration:
            return
        if token[0] == ']':
            break
        if token == ('', ''):
            continue
        signature.append(token[0] or '-')
    signature = ''.join(signature)
    return signature
''',
    'C2_shared_entry_peer': '''def go(dates, check):
    for date in dates:
        try:
            if len(date) != 8 and date.isdigit():
                check(date)
        except AssertionError:
            pass
    return dates
''',
    'C3_genuine_else_chain': '''def g(a, b):
    if a == 1:
        return 'x'
    elif b == 2:
        return 'y'
    else:
        z = a + b
        return z
''',
    'C4_armfall_noloop': '''def h(tok, out):
    if tok is None:
        return
    if tok == '':
        return
    if tok.startswith('@'):
        out['k'] = tok
    out['v'] = tok
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
        v120_py = OUT + '/%s_out_v120.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v120_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v120_py,'rb').read()
        py_compile.compile(v120_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
        with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
        with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
        ok = byte_equal(orig, prod)
        summary.append((cid, same, ok))
        print('%-24s text_same=%-5s v120_byte_equal=%s' % (cid, same, ok))

    E = {'E1_armfall_quote'}  # E2 实测 HEAD 本已正确（SUBSCR 臂形态不触发折叠），归控制
    verdicts = []
    for cid, same, ok in summary:
        if cid in E:
            v = 'PASS' if ((not same) and ok) else 'FAIL'
        else:
            v = 'PASS' if (same and ok) else 'FAIL'
        verdicts.append(v)
        print('verdict %-24s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
