# rr-v5r133 [v133-DEFLINE/DELSTMT] 变体矩阵（A/B 单文件交换：HEAD d39aac5e vs v133 工作树）
# 功效案：模块级多行 def 行锚 NOP 对 + 模块级 del 语句（IfRegion 条件块前导段提取器）
# 控制案：单行 def/函数体多行 def（v107 既有域）/函数内 del/Round-33 裸串（既有域）
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r133matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v133_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：模块级多行 def 签名（行锚 NOP 对）夹在其他 def 之间
    'E1_module_multiline_def': '''def helper_a(x):
    return x + 1

def wide(a, b, c='',
         d='', e=3):
    return a + b + c + d + e

def helper_b(y):
    return y * 2

X = 1
''',
    # 功效案：模块级 del 语句在 def 之前
    'E2_module_del_before_def': '''import os as _os

del _os

def after():
    return 42
''',
    # 控制案：单行 def（无行锚 NOP）
    'C1_single_line_def': '''def plain(a, b):
    return a + b

Y = 2
''',
    # 控制案：函数体内多行 def 前奏（v107 既有域）
    'C2_func_multiline_def': '''def outer(x):
    def inner(a, b,
              c=3):
        return a + b + c
    return inner(x, 2)
''',
    # 控制案：函数内 del（既有 DELETE 路径）
    'C3_func_del': '''def d():
    v = 1
    del v
    return 0
''',
    # 控制案：模块级裸串 + def（Round-33 既有域）
    'C4_module_barestring': '''"module doc"

def z():
    return 1
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
        v133_py = OUT + '/%s_out_v133.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v133_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v133_py,'rb').read()
        try:
            py_compile.compile(v133_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v133_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD 丢语句（TEXT-DIFF）→ v133 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    # E2 实测 HEAD 本已等价（无 if 宿主的模块 del 走其他路径）——归控制；
    # difflib 的 del re 位于巨型 IfRegion 条件块前导段（本轮 DELSTMT 分支修
    # 复，判官 module 单元 100% 实证）。功效案仅 E1。
    E = {'E1_module_multiline_def'}
    verdicts = []
    for cid, same, ok in summary:
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
