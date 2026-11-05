# rr-v5r119 [v119-TRYTOP] 变体矩阵（A/B 文件交换：HEAD 2df7f6ba vs v119 工作树）
# 功效案：循环体顶 try（while 1 头直接后继），除臂带 return——
#   HEAD 因 _use_if_tiebreaker 虚假区间覆盖把 try 错挂循环体内 IfRegion，
#   try 漏渲染、兜底扫尾搬到循环底且 handler return 降级 pass（真实 R1）
# 控制案：无循环 try / if 臂内 try / 共享入口 peer（get_opt_objects 族）/
#   for 体顶 try / 条件 while 体顶 try
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r119matrix'
ANA = REPO + '/core/cfg/region_analyzer.py'
V119_COPY = OUT + '/region_analyzer_v119.py'
PY = 'D:/Python/python.exe'
shutil.copy(ANA, V119_COPY)

CASES = {
    # ---- 功效案 ----
    'E1_trytop_while1': '''def p(next, token, signature):
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
    'E2_trytop_valret': '''def q(next, token):
    out = []
    while 1:
        try:
            token = next()
        except StopIteration:
            return None
        if token == 'x':
            break
        out.append(token)
    return out
''',
    'E3_trytop_handler_stmts': '''def r(next, token, log):
    while 1:
        try:
            token = next()
        except StopIteration:
            log.append('done')
            return
        if token is None:
            break
        log.append(token)
    return log
''',
    # ---- 控制案 ----
    'C1_try_noloop': '''def a(g):
    try:
        v = g()
    except StopIteration:
        return None
    return v
''',
    'C2_try_in_if_arm': '''def b(g, x, out):
    if x:
        try:
            out.append(g())
        except ValueError:
            return None
    return out
''',
    'C3_shared_entry_peer': '''def go(dates, check):
    for date in dates:
        try:
            if len(date) != 8 and date.isdigit():
                check(date)
        except AssertionError:
            pass
    return dates
''',
    'C4_try_in_for_top': '''def c(g, out):
    for i in range(3):
        try:
            out.append(g())
        except KeyError:
            return out
    return out
''',
    'C5_try_in_while_cond': '''def d(g, out, n):
    while n > 0:
        try:
            out.append(g())
        except IndexError:
            return out
        n -= 1
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

    head_export = OUT + '/region_analyzer_head.py'
    r = subprocess.run(['git', '-C', REPO, 'show', 'HEAD:core/cfg/region_analyzer.py'], capture_output=True)
    open(head_export, 'wb').write(r.stdout)

    summary = []
    for cid in CASES:
        head_py = OUT + '/%s_out_head.py' % cid
        v119_py = OUT + '/%s_out_v119.py' % cid
        shutil.copy(head_export, ANA)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        shutil.copy(V119_COPY, ANA)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v119_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v119_py,'rb').read()
        py_compile.compile(v119_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
        with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
        with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
        ok = byte_equal(orig, prod)
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v119_byte_equal=%s' % (cid, same, ok))

    E = {'E1_trytop_while1'}  # E2/E3 实测 HEAD 本已正确（病形需 break+continue
    # 的 if 链产生虚假 If 候选），归为控制案 C6/C7
    verdicts = []
    for cid, same, ok in summary:
        if cid in E:
            v = 'PASS' if ((not same) and ok) else 'FAIL'
        else:
            v = 'PASS' if (same and ok) else 'FAIL'
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
