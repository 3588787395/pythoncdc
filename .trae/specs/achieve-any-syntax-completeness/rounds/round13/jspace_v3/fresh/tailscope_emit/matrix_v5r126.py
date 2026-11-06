# rr-v5r126 [v126-TAIL] 变体矩阵（A/B 单文件交换：HEAD 4811d386 vs v126 工作树）
# 功效案：E1 iterfind 同构（while 1 + 宿主 try + 双内层 try + 尾赋值）——v125 轮
#   OBSERVE（结构还原、尾块 try 外）→ 本轮 BYTE-EQUAL 目标
# 控制案：E1b 无环直落尾（普通 try/except 后语句——绝不可吞）/ C1-C4 既有域
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r126matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v126_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    'E1_iterfind_shape': '''def f(next, token, selector, ops, _cache, ck):
    try:
        selector = _cache[ck]
    except KeyError:
        if len(_cache) > 100:
            _cache.clear()
        next = iter(token).__next__
        try:
            token = next()
        except StopIteration:
            return None
        selector = []
        while 1:
            try:
                selector.append(ops[token[0]](next, token))
            except StopIteration:
                raise SyntaxError('invalid path') from None
            try:
                token = next()
                if token[0] == "/":
                    token = next()
            except StopIteration:
                break
        _cache[ck] = selector
    return selector
''',
    'E1b_plain_tail_noabsorb': '''def g(a, b):
    try:
        v = a / b
    except ZeroDivisionError:
        v = 0
    return v + 1
''',
    'C1_while1_trytop': '''def h(next, token, out):
    while 1:
        try:
            token = next()
        except StopIteration:
            return None
        if token == "]":
            break
        out.append(token)
    return out
''',
    'C2_try_in_try_noloop': '''def i(a, b):
    try:
        try:
            v = a / b
        except ZeroDivisionError:
            v = 0
    except TypeError:
        v = -1
    return v
''',
    'C3_loop_body_try_break': '''def j(items, lim):
    out = []
    for it in items:
        try:
            v = it[0]
        except IndexError:
            break
        if v > lim:
            continue
        out.append(v)
    return out
''',
    'C4_nested_while_try': '''def k(n):
    total = 0
    while n > 0:
        try:
            total += n % 3
        except ArithmeticError:
            return -1
        n -= 1
    return total
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
        v126_py = OUT + '/%s_out_v126.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v126_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v126_py,'rb').read()
        py_compile.compile(v126_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
        with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
        with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
        ok = byte_equal(orig, prod)
        summary.append((cid, same, ok))
        print('%-26s text_same=%-5s v126_byte_equal=%s' % (cid, same, ok))
    # E1: 功效案（HEAD 拆臂丢体 → v126 全还原 BYTE-EQUAL）
    # E1b/C*: 控制案（零漂移 + BYTE-EQUAL）
    E = {'E1_iterfind_shape'}
    verdicts = []
    for cid, same, ok in summary:
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-26s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
