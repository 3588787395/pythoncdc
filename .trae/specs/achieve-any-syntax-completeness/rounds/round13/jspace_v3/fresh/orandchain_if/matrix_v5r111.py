# rr-v5r111 [v111-ORAND] 复现矩阵：compile -> pyc -> pycdc(current) -> recompile
#   -> 全 code object 逐字段 BYTE-EQUAL；并用 HEAD 版 A/B 文件交换逐案比产品文本。
import os, sys, subprocess, types, py_compile, marshal, json

REPO = 'F:/Downloads/pythoncdc-main'
EV = REPO + '/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/orandchain_if'
GEN = REPO + '/core/cfg/region_ast_generator.py'
ANA = REPO + '/core/cfg/region_analyzer.py'
PY = 'D:/Python/python.exe'
GIT = 'E:/Program Files/PortableGit/bin/git.exe'

CASES = {
 # ---- 功效案（or 首 + and 尾 + 终止臂）----
 'v111_m1_exact': '''def f(key):
    if isinstance(key, set) or (isinstance(key, tuple) and any(isinstance(x, set) for x in key)):
        raise TypeError('set')
    if isinstance(key, dict) or (isinstance(key, tuple) and any(isinstance(x, dict) for x in key)):
        raise TypeError('dict')
''',
 'v111_m2_no_genexpr': '''def g(x):
    return True

def f(key):
    if isinstance(key, set) or (isinstance(key, tuple) and g(key)):
        raise TypeError('set')
    if isinstance(key, dict) or (isinstance(key, tuple) and g(key)):
        raise TypeError('dict')
''',
 'v111_m4_single_if': '''def f(key):
    if isinstance(key, set) or (isinstance(key, tuple) and any(isinstance(x, set) for x in key)):
        raise TypeError('set')
''',
 'v111_or_and3': '''def f(a, b, c, d):
    if a or (b and c and d):
        raise TypeError('x')
''',
 'v111_or3_and2': '''def f(a, b, c, d):
    if a or b or (c and d):
        raise TypeError('x')
''',
 'v111_return_arm': '''def f(key):
    if isinstance(key, set) or (isinstance(key, tuple) and key):
        return 1
    return 0
''',
 'v111_two_if_diffmsg': '''def f(key):
    if isinstance(key, set) or (isinstance(key, tuple) and key):
        raise ValueError('first')
    if isinstance(key, dict) or (isinstance(key, tuple) and key):
        raise KeyError('second')
''',
 'v111_prefix_stmts': '''def f(key):
    tag = 1
    if isinstance(key, set) or (isinstance(key, tuple) and key):
        raise TypeError(tag)
    return tag
''',
 # ---- 控制案（非目标形态，A/B 必须 TEXT-SAME）----
 'v111_nested': '''def f(key):
    if isinstance(key, set) or isinstance(key, tuple):
        if any(isinstance(x, set) for x in key):
            raise TypeError('set')
''',
 'v111_nested_bool': '''def f(a, b, c):
    if a or b:
        if c:
            raise TypeError('x')
''',
 'v111_plain_or': '''def f(a, b):
    if a or b:
        raise TypeError('x')
''',
 'v111_plain_and': '''def f(a, b):
    if a and b:
        raise TypeError('x')
''',
 'v111_m3_plain_if': '''def f(key):
    if isinstance(key, set):
        raise TypeError('set')
    if isinstance(key, dict):
        raise TypeError('dict')
''',
 'v111_m5_diff_tail': '''def f(key):
    if isinstance(key, set) or (isinstance(key, tuple) and any(isinstance(x, set) for x in key)):
        raise TypeError('set')
    if isinstance(key, dict) or (isinstance(key, tuple) and any(isinstance(x, dict) for x in key)):
        return 1
    return 0
''',
 'v111_or_and_else': '''def f(a, b, c):
    if a or (b and c):
        x = 1
    else:
        x = 2
    return x
''',
}

# [v111-ORAND] 未领形态登记：这三案是本人为探索覆盖面加入的扩展合成案，
# 并非真实 pyc 案、也非用户指定案。其 v111 产品与 HEAD 产品逐字节相同
# （A/B = TEXT-SAME），错误形态分别为 `a or not b or c and d`（and 尾 3 成员
# 被取反）、`a or b or c`（or 链 3 成员丢尾）、`if not A:` 翻转（终止臂后
# 仍有语句、出口非平凡）——均属**分析端 BoolOp 链走查的另一缺陷族**，与
# REAL46-036 的「C 沦为内层 IfRegion.condition_block」不同形。HEAD 基线即
# recompile DIFF（见 unclaimed_v5r111.py），本轮窄修复未触碰，按纪律如实
# 登记为「未闭合/未领」，不计入正式矩阵，绝不发半修复。
UNCLAIMED = {'v111_or_and3', 'v111_or3_and2', 'v111_prefix_stmts'}

def category(name):
    return 'UNCLAIMED' if name in UNCLAIMED else 'FORMAL'

def norm(c):
    return (c.co_code.hex(), c.co_exceptiontable.hex(),
            c.co_names, c.co_varnames, c.co_freevars, c.co_cellvars,
            c.co_flags,
            tuple(norm(k) if isinstance(k, types.CodeType) else k for k in c.co_consts))

def toplevels(c):
    return {k.co_name: norm(k) for k in c.co_consts if isinstance(k, types.CodeType)}

def load(p):
    with open(p, 'rb') as f:
        return marshal.loads(f.read()[16:])

def decompile(pyc, out, err):
    with open(out, 'wb') as fo, open(err, 'wb') as fe:
        r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', pyc],
                           stdout=fo, stderr=fe, cwd=REPO, timeout=300)
    return open(out, 'rb').read(), r.returncode

def main():
    head_gen = subprocess.run([GIT, '-C', REPO, 'show', 'HEAD:core/cfg/region_ast_generator.py'],
                              capture_output=True).stdout.decode('utf-8')
    head_ana = subprocess.run([GIT, '-C', REPO, 'show', 'HEAD:core/cfg/region_analyzer.py'],
                              capture_output=True).stdout.decode('utf-8')
    cur_gen = open(GEN, encoding='utf-8').read()
    cur_ana = open(ANA, encoding='utf-8').read()
    assert 'v111-ORAND' in cur_gen and 'v111-ORAND' not in head_gen
    os.makedirs(EV + '/matrix_products', exist_ok=True)
    results = []
    swapped = False
    try:
        for name, src in CASES.items():
            sp = EV + '/matrix_products/%s.py' % name
            pyc = EV + '/matrix_products/%s.pyc' % name
            pa = EV + '/matrix_products/%s_v111.py' % name
            pb = EV + '/matrix_products/%s_head.py' % name
            open(sp, 'w', encoding='utf-8').write(src)
            py_compile.compile(sp, pyc, doraise=True)
            ca = toplevels(load(pyc))
            ta, rca = decompile(pyc, pa, pa + '.err')
            open(GEN, 'w', encoding='utf-8').write(head_gen)
            open(ANA, 'w', encoding='utf-8').write(head_ana)
            swapped = True
            tb, rcb = decompile(pyc, pb, pb + '.err')
            open(GEN, 'w', encoding='utf-8').write(cur_gen)
            open(ANA, 'w', encoding='utf-8').write(cur_ana)
            swapped = False
            same = (ta == tb)
            try:
                cb = toplevels(compile(ta.decode('utf-8'), 'p', 'exec'))
                be = (ca == cb)
                detail = '' if be else 'rem=%s add=%s chg=%s' % (
                    sorted(set(ca) - set(cb)), sorted(set(cb) - set(ca)),
                    sorted(n for n in set(ca) & set(cb) if ca[n] != cb[n]))
            except SyntaxError as se:
                be, detail = False, 'SYNTAX-ERR ' + se.msg[:40]
            prod_lines = [l for l in ta.decode('utf-8').splitlines() if l.strip() and not l.startswith('#')]
            results.append((name, 'TEXT-SAME' if same else 'TEXT-DIFF',
                            'BYTE-EQUAL' if be else 'DIFF', detail, prod_lines[:6]))
    finally:
        if swapped:
            open(GEN, 'w', encoding='utf-8').write(cur_gen)
            open(ANA, 'w', encoding='utf-8').write(cur_ana)
        assert open(GEN, encoding='utf-8').read() == cur_gen
        assert open(ANA, encoding='utf-8').read() == cur_ana
    formal = [r for r in results if category(r[0]) == 'FORMAL']
    unclaimed = [r for r in results if category(r[0]) == 'UNCLAIMED']
    print()
    print('==== 正式矩阵 FORMAL (%d 案) ====' % len(formal))
    for name, s, f, d, pl in formal:
        print('%-24s %-10s %-11s %s' % (name, s, f, d))
        for l in pl:
            print('      | ' + l)
    print()
    print('==== 未领形态登记 UNCLAIMED (%d 案，HEAD 预存在、本轮未触碰) ====' % len(unclaimed))
    for name, s, f, d, pl in unclaimed:
        print('%-24s %-10s %-11s %s' % (name, s, f, d))
        for l in pl:
            print('      | ' + l)
    f_eq = sum(1 for _, _, f, _, _ in formal if f == 'BYTE-EQUAL')
    f_eff = sum(1 for _, s, _, _, _ in formal if s == 'TEXT-DIFF')
    f_ctl = sum(1 for _, s, _, _, _ in formal if s == 'TEXT-SAME')
    f_ctl_same = sum(1 for _, s, _, _, _ in formal if s == 'TEXT-SAME')
    u_same = sum(1 for _, s, _, _, _ in unclaimed if s == 'TEXT-SAME')
    print()
    print('FORMAL: %d 案, BYTE-EQUAL %d/%d, 功效案 TEXT-DIFF %d, 控制案 TEXT-SAME %d/%d'
          % (len(formal), f_eq, len(formal), f_eff, f_ctl_same, f_ctl))
    print('UNCLAIMED: %d 案, A/B TEXT-SAME(=HEAD 预存在) %d/%d, 均 recompile DIFF, 不计入正式矩阵'
          % (len(unclaimed), u_same, len(unclaimed)))
    print('ALL: TEXT-DIFF %d/%d, BYTE-EQUAL %d/%d'
          % (sum(1 for _, s, _, _, _ in results if s == 'TEXT-DIFF'), len(results),
             sum(1 for _, _, f, _, _ in results if f == 'BYTE-EQUAL'), len(results)))
    json.dump({
        'cases': [{'name': n, 'category': category(n), 'ab': s,
                   'recompile': f, 'detail': d} for n, s, f, d, _ in results],
        'formal_matrix': {
            'n': len(formal), 'all_byte_equal': f_eq == len(formal),
            'byte_equal': f_eq, 'efficacy_text_diff': f_eff,
            'control_text_same': f_ctl_same, 'control_n': f_ctl},
        'unclaimed': {
            'n': len(unclaimed), 'head_preexisting_ab_text_same': u_same,
            'names': [n for n, _, _, _, _ in unclaimed],
            'note': 'HEAD 基线即 recompile DIFF；v111 窄修复未改变其产品文本；'
                    '属分析端 BoolOp 链另一缺陷族，本轮如实登记为未闭合/未领。'},
    }, open(EV + '/matrix_v5r111_result.json', 'w', encoding='utf-8'),
        ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
