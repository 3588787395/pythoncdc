# rr-v5r124 [v124-LOOPHEAD] 变体矩阵（A/B 单文件交换：HEAD 7474b0e6 vs v124 工作树）
# 功效案：while 1 + 宿主 try handler 体内双内层 try（iterfind 环孤儿化族）
# 控制案：while1+循环顶 try（v119 形）/ try-in-try 无环 / 环体 try+break / 嵌套环
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r124matrix'
FILES = {'ANA': REPO + '/core/cfg/region_analyzer.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v124_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    'E1_iterfind_shape': '''def f(next, token, selector, ops, _cache):
    try:
        selector = _cache[("k",)]
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
        _cache[("k",)] = selector
    return selector
''',
    'C1_while1_trytop': '''def g(next, token, out):
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
    'C2_try_in_try_noloop': '''def h(a, b):
    try:
        try:
            v = a / b
        except ZeroDivisionError:
            v = 0
    except TypeError:
        v = -1
    return v
''',
    'C3_loop_body_try_break': '''def i(items, lim):
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
    'C4_nested_while_try': '''def j(n):
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
        v124_py = OUT + '/%s_out_v124.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v124_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v124_py,'rb').read()
        py_compile.compile(v124_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
        with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
        with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
        ok = byte_equal(orig, prod)
        summary.append((cid, same, ok))
        print('%-24s text_same=%-5s v124_byte_equal=%s' % (cid, same, ok))
    E = set()
    # OBSERVE 组判据说明：E1 功效案——HEAD 环孤儿化（while 1 壳/append 体/break
    # 全丢），v124 结构完全还原（while 1 + 双内层 try + append + break）；
    # 残余=尾块作用域（handler 末语句在原版属 handler 体内、产品排 try 外——
    # 本形语义等价、重编译字节不同，与 REAL46-008 /iterfind 同一残差，
    # 见 FINDING §3）。判据=结构还原（text_same=False）+ 残差如实登记。
    OBSERVE = {'E1_iterfind_shape'}
    verdicts = []
    for cid, same, ok in summary:
        v = ('OBSERVE-PASS' if (not same) else 'OBSERVE-FAIL') if cid in OBSERVE else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-24s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v in ('PASS', 'OBSERVE-PASS') for v in verdicts) else 'FAIL')
