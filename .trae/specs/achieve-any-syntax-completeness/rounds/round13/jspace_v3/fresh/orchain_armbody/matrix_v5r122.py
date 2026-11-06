# rr-v5r122 [v122-ORCHAIN] 变体矩阵（A/B 两文件交换：HEAD 02a529d3 vs v122 工作树）
# 功效案：or 前缀 + 内层 or 段 + 否定 and 尾成员 混合嵌套链（拆臂丢体族）
# 控制案：既有全部 boolop 重建器路径（R65 直连 and 尾 / 显式分组 / and-inner-or /
#   keeppop / skipedge / B98 边界 / R14c not(or) / B108 混合极性 / 纯链 / while 域）
import os, sys, subprocess, marshal, py_compile, shutil

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r122matrix'
FILES = {
    'ANA': REPO + '/core/cfg/region_analyzer.py',
    'RAG': REPO + '/core/cfg/region_ast_generator.py',
}
PY = 'D:/Python/python.exe'
COPIES = {k: OUT + '/v122_%s.py' % k for k in FILES}
for k, p in FILES.items():
    shutil.copy(p, COPIES[k])

CASES = {
    # ---- 功效案 ----
    'E1_orchain_armbody': '''def f(sig, pred):
    if sig == 'a' or sig == 'b' or ((sig == 'c' or sig == 'd') and not pred.isdigit()):
        tag = pred[0]
        return tag
    if sig == 'e':
        return 'E'
    else:
        raise ValueError('bad')
''',
    'E2_orchain_armbody_noret': '''def f(sig, pred):
    if sig == 'a' or sig == 'b' or ((sig == 'c' or sig == 'd') and not pred.isdigit()):
        tag = pred[0]
    if sig == 'e':
        return 'E'
    else:
        raise ValueError('bad')
    return tag
''',
    # ---- 控制案 ----
    'C1_or_tail_andgroup': '''def g(a, b, c, d):
    if a or b or (c and d):
        return 1
    return 0
''',
    'C2_nested_or_groups': '''def h(a, b, c, d):
    if (a or b) and (c or d):
        return 1
    return 0
''',
    'C3_and_inner_or': '''def i(a, b, c):
    if a and (b or c):
        return 1
    return 0
''',
    'C4_or_and_or': '''def j(a, b, c, d):
    if a or (b and c) or d:
        return 1
    return 0
''',
    'C5_pure_or3': '''def k(a, b, c):
    if a or b or c:
        return 1
    return 0
''',
    'C6_keeppop': '''def l(a, b, c, d):
    if a or (b and (c or d)):
        return 1
    return 0
''',
    'C7_skipedge': '''def m(a, b, c, d, e):
    if (a or (b and c)) and (d or e):
        return 1
    return 0
''',
    'C8_not_or': '''def n(a, b):
    if not (a or b):
        return 1
    return 0
''',
    'C9_or_not_member': '''def o(a, b):
    if a or not b:
        return 1
    return 0
''',
    'C10_tail_value_boundary': '''def p(a, b, c, d, e):
    if (a or b) and (c or d) and e:
        return 1
    return 0
''',
    'C11_orchain_in_while': '''def q(next, token, signature, predicate, re):
    while 1:
        try:
            token = next()
        except StopIteration:
            return None
        if token[0] == ']':
            break
        elif token == ('', ''):
            continue
        else:
            signature.append(token[0] or '-')
            predicate.append(token[1])
    signature = ''.join(signature)
    if signature == '-':
        return 1
    elif signature == ".='" or signature == ".!='" or ((signature == "-='" or signature == "-!='") and not re.match('\\\\-?\\\\d+$', predicate[0])):
        tag = predicate[0]
        return tag
    else:
        raise ValueError('bad')
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
        v122_py = OUT + '/%s_out_v122.py' % cid
        for k, p in FILES.items():
            shutil.copy(head_exports[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', head_py], capture_output=True, cwd=REPO, timeout=120)
        for k, p in FILES.items():
            shutil.copy(COPIES[k], p)
        subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/%s.pyc' % cid, '-o', v122_py], capture_output=True, cwd=REPO, timeout=120)
        same = open(head_py,'rb').read() == open(v122_py,'rb').read()
        py_compile.compile(v122_py, cfile=OUT + '/%s_re.pyc' % cid, doraise=True)
        with open(OUT + '/%s.pyc' % cid,'rb') as f: f.read(16); orig = marshal.load(f)
        with open(OUT + '/%s_re.pyc' % cid,'rb') as f: f.read(16); prod = marshal.load(f)
        ok = byte_equal(orig, prod)
        summary.append((cid, same, ok))
        print('%-28s text_same=%-5s v122_byte_equal=%s' % (cid, same, ok))

    E = {'E1_orchain_armbody', 'C11_orchain_in_while'}
    # OBSERVE 组判据说明：
    # - E2: 臂体不退出的功效变体，判据=v122 重编译 byte_equal（与 HEAD 文本是否
    #   漂移不设要求，实测 OBSERVE-PASS）。
    # - C6/C7: keeppop/skipedge 重建器控制案——两案为 HEAD 前已存在字节残余
    #   （实测 HEAD 产物 byte_equal=False，见 r122matrix/head 复核），非 v122
    #   回归；本轮判据=A/B 零漂移（text_same=True）。
    OBSERVE = {'E2_orchain_armbody_noret', 'C6_keeppop', 'C7_skipedge'}
    verdicts = []
    for cid, same, ok in summary:
        if cid in E:
            v = 'PASS' if ((not same) and ok) else 'FAIL'
        elif cid in OBSERVE:
            if cid == 'E2_orchain_armbody_noret':
                v = 'OBSERVE-PASS' if ok else 'OBSERVE-FAIL'
            else:
                v = 'OBSERVE-PASS' if same else 'OBSERVE-FAIL'
        else:
            v = 'PASS' if (same and ok) else 'FAIL'
        verdicts.append(v)
        print('verdict %-28s %s' % (cid, v))
    hard = [v for cid, v in zip([s[0] for s in summary], verdicts) if not v.startswith('OBSERVE')]
    print('MATRIX:', 'ALL PASS' if all(v == 'PASS' for v in hard) else 'FAIL',
          '| observe:', [v for v in verdicts if v.startswith('OBSERVE')])
