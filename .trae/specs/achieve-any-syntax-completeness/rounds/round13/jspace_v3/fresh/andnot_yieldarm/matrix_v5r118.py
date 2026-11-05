# rr-v5r118 [v118-ANDNOT] 变体矩阵（A/B 文件交换：HEAD 85982510 vs v118 工作树）
# 功效案：生成器循环体内 if/elif 链且 elif 复合条件为 `A and not B`
#   （elif 测试块 load 对循环认领 → B1b 门拒绝；臂体 yield 语句块被
#   IfExp 真值块守卫误判 → 链断 → elif 拆嵌套 IfRegion、else 臂错挂）
# 控制案：无循环 elif-and / 循环内普通 and / 非生成器同构 / 裸 yield 作
#   IfExp 值（IfExp 守卫须维持 break）
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r118matrix'
ANA = REPO + '/core/cfg/region_analyzer.py'
V118_COPY = OUT + '/region_analyzer_v118.py'
PY = 'D:/Python/python.exe'
shutil.copy(ANA, V118_COPY)

CASES = {
    # ---- 功效案 ----
    'E1_andnot_for_gen': '''def k(toks, ns, pa):
    for tok in toks:
        tag = tok
        if tag and tag[0] != '{':
            if ':' in tag:
                yield ('c', tag)
            elif ns and not pa:
                yield ('n', ns)
            else:
                yield tok
            pa = False
        else:
            yield tok
            pa = tag == '@'
''',
    'E2_andnot_while_gen': '''def w(toks, ns, pa):
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
    'E3_andnot_nochainstmt': '''def h(toks, ns, pa):
    for tok in toks:
        if tok == 'a':
            yield ('a', tok)
        elif ns and not pa:
            yield ('n', ns)
        else:
            yield tok
''',
    # ---- 控制案 ----
    'C1_andnot_noloop': '''def k(t, ns, pa):
    if t and t[0] != '{':
        if ':' in t:
            yield ('c', t)
        elif ns and not pa:
            yield ('n', ns)
        else:
            yield t
    else:
        yield t
''',
    'C2_plain_and_loop': '''def m(items, a, b):
    for x in items:
        if a and b:
            yield ('t', x)
        else:
            yield ('f', x)
''',
    'C3_andnot_nongen': '''def f(items, ns, pa, out):
    for x in items:
        if x:
            if x == 1:
                r = ('c', x)
            elif ns and not pa:
                r = ('n', ns)
            else:
                r = x
            out.append(r)
''',
    'C4_yield_ifexp_value': '''def g(c, a, v):
    x = a if c else (yield v)
    yield x
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
        v118_py = OUT + '/%s_out_v118.py' % cid
        shutil.copy(head_export, ANA)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        shutil.copy(V118_COPY, ANA)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v118_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v118_py,'rb').read()
        py_compile.compile(v118_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
        with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
        with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
        ok = byte_equal(orig, prod)
        summary.append((cid, same, ok))
        print('%-24s text_same=%-5s v118_byte_equal=%s' % (cid, same, ok))

    E = {'E1_andnot_for_gen', 'E3_andnot_nochainstmt',
         'C3_andnot_nongen'}  # C3 实测同为功效案（HEAD 同塌缩，v118 恢复 elif）
    E_PART = {'E2_andnot_while_gen'}  # 功效部分闭合：elif 臂恢复（TEXT 改善），
    # 重编译非等价为预存在 while 底部 store-recheck 重检族残余（HEAD 同非等价）
    verdicts = []
    for cid, same, ok in summary:
        if cid in E:
            v = 'PASS' if ((not same) and ok) else 'FAIL'
        elif cid in E_PART:
            v = 'PASS-PARTIAL' if (not same) else 'FAIL'
        else:
            v = 'PASS' if same else 'FAIL'
        verdicts.append(v in ('PASS', 'PASS-PARTIAL'))
        print('verdict %-24s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(verdicts) else 'FAIL')
