# rr-v5r130 [v130-EXCASSERT/ASSERTNOT] 变体矩阵（A/B 单文件交换：HEAD 473ac054 vs v130 工作树）
# 功效案：except 处理器内 assert（AssertRegion 派发白名单补位 + IF_FALSE 极性还原）
# 控制案：手写 if+raise（判别器健全性）/ 非 handler 域（B135/x08 既有域）/ None 检查域
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r130matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v130_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：statistics._exact_ratio 精确形（assert not X + 后续 return）
    'E1_assert_not_in_handler': '''def er(x, _isfinite):
    try:
        return x.as_integer_ratio()
    except AttributeError:
        pass
    except (OverflowError, ValueError):
        assert not _isfinite(x)
        return (x, None)
    try:
        return (x.numerator, x.denominator)
    except AttributeError:
        raise TypeError("bad")
''',
    # 功效案：assert X（IF_TRUE 极性）+ 后续语句
    'E2_assert_true_in_handler': '''def at(v, lim):
    try:
        return v / lim
    except ZeroDivisionError:
        assert v >= 0
        return 0.0
''',
    # 功效案：assert 为 handler 末语句
    'E3_assert_last_in_handler': '''def al(v):
    try:
        return int(v)
    except ValueError:
        assert v
''',
    # 功效案：assert 带消息
    'E4_assert_msg_in_handler': '''def am(v):
    try:
        return v.key
    except AttributeError:
        assert v is not None, "v required"
        return None
''',
    # 控制案：手写 if + raise AssertionError（LOAD_GLOBAL 判别器——绝不可变 assert）
    'C1_handwritten_raise': '''def hr(x, _isfinite):
    try:
        return x.ratio()
    except (OverflowError, ValueError):
        if _isfinite(x):
            raise AssertionError
        else:
            return (x, None)
''',
    # 控制案：非 handler 域 assert（B135/x08 既有域，零漂移）
    'C2_assert_in_if': '''def ai(x, lim):
    if x > lim:
        assert x < 100
        return x
    return 0
''',
    # 控制案：普通函数体 assert（AssertRegion 主路径既有形）
    'C3_assert_plain': '''def ap(x):
    assert x != 0
    return 1 / x
''',
    # 控制案：try 体（非 handler）内 assert
    'C4_assert_in_try_body': '''def tb(x):
    try:
        assert x
        return 1
    except AssertionError:
        return 0
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
        v130_py = OUT + '/%s_out_v130.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v130_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v130_py,'rb').read()
        try:
            py_compile.compile(v130_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v130_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD if/raise 展开（TEXT-DIFF）→ v130 assert 还原 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    E = {'E1_assert_not_in_handler', 'E2_assert_true_in_handler',
         'E3_assert_last_in_handler', 'E4_assert_msg_in_handler'}
    verdicts = []
    for cid, same, ok in summary:
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
