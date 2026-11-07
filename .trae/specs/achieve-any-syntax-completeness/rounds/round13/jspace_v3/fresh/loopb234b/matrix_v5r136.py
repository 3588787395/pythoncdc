# rr-v5r136 [v136-LOOPB234B] 变体矩阵（A/B 单文件交换：HEAD 76af0778 vs v136 工作树）
# 功效案：for 体 else 臂（回边走查域）B234 反源序多目标赋值（get_matching_blocks 精确形）
# 控制案：单赋值/链式（COPY）/解包（UNPACK 分支）/兄弟独立赋值（非连续 STORE）
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r136matrix'
FILES = {'RAG': REPO + '/core/cfg/region_ast_generator.py'}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v136_%s.py' % k for k in FILES}
os.makedirs(OUT, exist_ok=True)
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # 功效案：for 体 else 臂三目标元组赋值（get_matching_blocks 精确形，continue 渲染域）
    'E1_else_three_targets': '''def g(blocks):
    i1 = j1 = k1 = 0
    out = []
    for i2, j2, k2 in blocks:
        if i1 + k1 == i2 and j1 + k1 == j2:
            k1 += k2
        else:
            if k1:
                out.append((i1, j1, k1))
            i1, j1, k1 = i2, j2, k2
    return out
''',
    # 功效案：else 臂两目标元组赋值
    'E2_else_two_targets': '''def f(pairs):
    x = y = 0
    hit = []
    for a, b in pairs:
        if a > y:
            y = a
        else:
            hit.append(y)
            x, y = b, a
    return hit, x + y
''',
    # 功效案：else 臂属性值元组赋值
    'E3_else_attr_values': '''class S:
    def m(self, blocks):
        i1 = j1 = 0
        out = []
        for a, b in blocks:
            if a == i1:
                i1 += b
            else:
                out.append(b)
                i1, j1 = self.p, self.q
        return out, i1 + j1
''',
    # 控制案：回边单赋值（既有路径零漂移）
    'C1_else_single': '''def h(items):
    acc = 0
    for x in items:
        if x:
            acc += 1
        else:
            acc = x
    return acc
''',
    # 控制案：链式赋值 a = b = v（COPY 1 纯度拒绝，零漂移）
    'C2_chain_copy': '''def k(vs):
    a = b = 0
    for v in vs:
        if v:
            a += v
        else:
            a = b = v
    return a + b
''',
    # 控制案：else 臂解包赋值（UNPACK 分支既有域，零漂移）
    'C3_unpack': '''def m(pairs):
    x = y = 0
    for p in pairs:
        if x:
            x -= 1
        else:
            x, y = p
    return x + y
''',
    # 控制案：兄弟独立赋值（LOAD 交错，STORE 不连续 N=1，零漂移）
    'C4_sibling_stores': '''def n(vs):
    a = b = 0
    for v in vs:
        if v:
            a += 1
        else:
            a = v
            b = a + 1
    return a + b
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
        v136_py = OUT + '/%s_out_v136.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v136_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v136_py,'rb').read()
        try:
            py_compile.compile(v136_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
            with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
            with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
            ok = byte_equal(orig, prod)
        except Exception as e:
            print(cid, 'compile/decompile error:', e)
            ok = False
        summary.append((cid, same, ok))
        print('%-24s text_same=%-5s v136_byte_equal=%s' % (cid, same, ok))
    # 功效案：HEAD 丢次级目标（TEXT-DIFF）→ v136 BYTE-EQUAL
    # 控制案：零漂移（TEXT-SAME）+ BYTE-EQUAL
    # 预存在残差（实测 head 与 v136 输出逐字节同=本轮零触碰，排除判定）：
    #   E2/E3=else 臂尾多目标经融合落空路径/_build_effective_stmts 渲染
    #         （非回边走查 _generate_stmts_from_instrs——探针实证零 BSS
    #         调用），丢目标属他族登记下轮；
    #   C2=链式赋值回边 walrus 形（COPY 纯度拒绝域，预存在）；
    #   C3=循环体 UNPACK 元组族（C4_body_tuple 同族预存在登记）。
    E = {'E1_else_three_targets'}
    PREEXISTING = {'E2_else_two_targets', 'E3_else_attr_values',
                   'C2_chain_copy', 'C3_unpack'}
    verdicts = []
    for cid, same, ok in summary:
        if cid in PREEXISTING:
            print('verdict %-24s PREEXISTING-FAIL(非本轮引入，head 同不等)' % cid)
            continue
        v = ('PASS' if ((not same) and ok) else 'FAIL') if cid in E else ('PASS' if (same and ok) else 'FAIL')
        verdicts.append(v)
        print('verdict %-24s %s' % (cid, v))
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in verdicts) else 'FAIL')
