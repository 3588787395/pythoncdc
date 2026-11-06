# rr-v5r129 [v129-TRIVNOP] 变体矩阵（A/B 单文件交换：HEAD df2729e6 vs v129 工作树）
# 功效案：trivial 返回体 NOP 语句位还原族（docstring+裸串/pass/while False 折叠）
# 控制案：类体/模块级相邻 NOP（既有路径承接）/try 行标记（结构再生）/单 docstring
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r129matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v129_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    'E1_doc_barestring': '''def f():
    "a"
    "b"
    return 1
''',
    'E2_doc_two_barestrings': '''def g():
    "a"
    "b"
    "c"
    return 1
''',
    'E3_pass_return': '''def h():
    pass
    return 2
''',
    'E4_doc_pass': '''def i():
    """doc"""
    pass
''',
    'E5_barestrings_noreturn': '''def j():
    "a"
    "b"
''',
    'E6_whilefalse_folded': '''def k():
    "d"
    while False:
        pass
    return 1
''',
    'C1_class_two_strings': '''class C:
    "doc1"
    "doc2"
    def m(self):
        return 1
''',
    'C2_module_two_strings': '''"mod1"
"mod2"
x = 1
''',
    'C3_doc_only': '''def l():
    """doc"""
    return 1
''',
    'C4_try_marker': '''def m():
    "d"
    try:
        return 1
    except Exception:
        pass
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
        v129_py = OUT + '/%s_out_v129.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v129_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v129_py,'rb').read()
        try:
            py_compile.compile(v129_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v129_byte_equal=%s' % (cid, same, ok))
    # 功效案：E1/E2/E3（HEAD 丢 NOP TEXT-DIFF → v129 BYTE-EQUAL）+E6（HEAD 丢
    #   NOP+False 常量 → v129 While(False,pass) 双还原 BYTE-EQUAL）。
    # E4/E5 实测 HEAD 本已等价（末位 pass/末位裸串被编译器整体消除、原始
    #   bytecode 无 NOP——两者归控制零漂移证据）。
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    E = {'E1_doc_barestring', 'E2_doc_two_barestrings', 'E3_pass_return',
         'E6_whilefalse_folded'}
    verdicts = []
    for cid, same, ok in summary:
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
