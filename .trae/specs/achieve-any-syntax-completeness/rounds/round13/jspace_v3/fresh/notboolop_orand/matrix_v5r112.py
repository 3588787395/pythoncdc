# rr-v5r112 [v112-NOTBOOL] 复现矩阵：compile -> pyc -> pycdc(current) -> recompile
#   -> 全 code object 逐字段 BYTE-EQUAL；并用 HEAD 9139e4c3 版 A/B 文件交换
#   逐案比产品文本（功效案 TEXT-DIFF、控制案 TEXT-SAME）。
# 中间产物写 D:/temp/...（不落证据目录）。
import os, sys, subprocess, types, py_compile, marshal, json

REPO = 'F:/Downloads/pythoncdc-main'
EV = REPO + '/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/notboolop_orand'
MP = 'D:/temp/opencode/cl_layout/r112matrix'
GEN = REPO + '/core/cfg/region_ast_generator.py'
ANA = REPO + '/core/cfg/region_analyzer.py'
PY = 'D:/Python/python.exe'
GIT = 'E:/Program Files/PortableGit/bin/git.exe'
DIAG = 'D:/temp/opencode/cl_layout/r112diag_b'

# 功效案（本轮目标形态）：not(or+and) 值链双重取反 + or 真出口极性反
EFFICACY = {
 'm4_not': "def p(a, b):\n    r = not (a or b)\n    return r\n",
 'm5_hash': "def p(d):\n    ch = d.get('__hash__', None)\n    r = not (ch is None or (ch == 0 and '__eq__' in d))\n    return r\n",
 'm8_getfield': """def gf(cls, a_name, a_type, default_kw_only):
    default = getattr(cls, a_name, MISSING)
    if isinstance(default, Field):
        f = default
    else:
        if isinstance(default, types.MemberDescriptorType):
            default = MISSING
        f = field(default=default)
    f.name = a_name
    f.type = a_type
    f._field_type = _FIELD
    typing = sys.modules.get('typing')
    if typing:
        if _is_classvar(a_type, typing) or (isinstance(f.type, str) and _is_type(f.type, cls, typing, typing.ClassVar, _is_classvar)):
            f._field_type = _FIELD_CLASSVAR
    if f._field_type is _FIELD:
        dataclasses = sys.modules[__name__]
        if _is_initvar(a_type, dataclasses) or (isinstance(f.type, str) and _is_type(f.type, cls, dataclasses, dataclasses.InitVar, _is_initvar)):
            f._field_type = _FIELD_INITVAR
    if f._field_type in (_FIELD_CLASSVAR, _FIELD_INITVAR):
        if f.default_factory is not MISSING:
            raise TypeError('x')
    if f._field_type in (_FIELD, _FIELD_INITVAR):
        if f.kw_only is MISSING:
            f.kw_only = default_kw_only
    if f._field_type is _FIELD and f.default.__class__.__hash__ is None:
        raise ValueError('x')
    return f
""",
 'n8_not_or_and': "def p(a, b, c):\n    r = not (a or (b and c))\n    return r\n",
 # 真实源码含双层 not：HEAD 误渲三层 not，本轮按 k_cont=2 判据保真为双层
 'n8_notnot': "def p(a, b):\n    r = not not (a or b)\n    return r\n",
}

# 控制案（非目标形态，A/B 必须 TEXT-SAME）
CONTROL = {
 # for 循环内 or+and 且首块含前导 STORE 的形态覆盖案（HEAD 已正确，A/B TEXT-SAME）
 'n8_loop_or_and': """def p(items, A, B, C, out):
    for t in items:
        tag = 1
        if A(t) or (B(t) and C(t)):
            out.append(t)
            continue
        out.append(0)
    return out
""",
 'm1_or': "def p(a, b, x):\n    if a or b:\n        x = 1\n    return x\n",
 'm2_orand': "def p(a, b, c, x):\n    if a or (b and c):\n        x = 1\n    return x\n",
 'm3_getfield': "def p(t, a, b, c, f):\n    if t:\n        if a or (isinstance(b, str) and c(b)):\n            f.v = 1\n    return f\n",
 'm6_for': "def p(items, A, B):\n    out = []\n    seen = False\n    for name, t in items:\n        if A(t) or (isinstance(t, str) and B(t)):\n            seen = True\n        else:\n            out.append(t)\n    return out, seen\n",
 'm7_twoif': """def p(t, a, b, c, f):
    f.v = 0
    if t:
        if c(a) or (isinstance(b, str) and c(b)):
            f.v = 1
    if f.v in (0, 1):
        if c(a) or (isinstance(b, str) and c(b)):
            f.v = 2
    return f
""",
 # 真嵌套 if not A: if B and C（源码语义 not A and B and C）
 'n8_true_nested': "def p(a, b, c, f):\n    if not a:\n        if b and c:\n            f.v = 1\n    return f\n",
 # 正确 or + and 条件链（v111 族判据域）
 'n8_or_and': "def p(a, b, c, f):\n    if a or (b and c):\n        f.v = 1\n    return f\n",
 # v111 终止臂形态
 'n8_or_and_term': "def p(a, b, c, f):\n    if a or (b and c):\n        raise TypeError('x')\n    return f\n",
 # 内层 if 合并（typing and (or-and)）语义等价控制
 'n8_typing_merge': "def p(t, a, b, c, f):\n    if t:\n        if a or (isinstance(b, str) and c(b)):\n            f.v = 1\n    return f\n",
}

CASES = dict(EFFICACY)
CASES.update(CONTROL)


def norm(c):
    return (c.co_code.hex(), c.co_exceptiontable.hex(),
            c.co_names, c.co_varnames, c.co_freevars, c.co_cellvars,
            c.co_flags,
            tuple(norm(k) if isinstance(k, types.CodeType) else k for k in c.co_consts))


def flat(c, prefix=''):
    out = {prefix + c.co_name: c}
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            out.update(flat(k, prefix + c.co_name + '.'))
    return out


def load(p):
    with open(p, 'rb') as f:
        return marshal.loads(f.read()[16:])


def decompile(pyc, out, err):
    with open(out, 'wb') as fo, open(err, 'wb') as fe:
        r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', pyc],
                           stdout=fo, stderr=fe, cwd=REPO, timeout=300)
    return open(out, 'rb').read(), r.returncode


def main():
    head_gen = subprocess.run([GIT, '-C', REPO, 'show',
                               '9139e4c3:core/cfg/region_ast_generator.py'],
                              capture_output=True).stdout.decode('utf-8')
    head_ana = subprocess.run([GIT, '-C', REPO, 'show',
                               '9139e4c3:core/cfg/region_analyzer.py'],
                              capture_output=True).stdout.decode('utf-8')
    cur_gen = open(GEN, encoding='utf-8').read()
    cur_ana = open(ANA, encoding='utf-8').read()
    assert 'v112-NOTBOOL' in cur_gen and 'v112-NOTBOOL' not in head_gen
    assert 'v111-ORAND' in head_gen, 'HEAD 应含 v111 修复'
    os.makedirs(MP, exist_ok=True)
    results = []
    swapped = False
    try:
        for name, src in CASES.items():
            sp = MP + '/%s.py' % name
            pyc = MP + '/%s.pyc' % name
            pa = MP + '/%s_v112.py' % name
            pb = MP + '/%s_head.py' % name
            open(sp, 'w', encoding='utf-8').write(src)
            py_compile.compile(sp, pyc, doraise=True)
            ca = {n: norm(c) for n, c in flat(load(pyc)).items()}
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
                cb = {n: norm(c) for n, c in flat(compile(ta.decode('utf-8'), 'p', 'exec')).items()}
                be = (ca == cb)
                detail = '' if be else 'rem=%s add=%s chg=%s' % (
                    sorted(set(ca) - set(cb)), sorted(set(cb) - set(ca)),
                    sorted(n for n in set(ca) & set(cb) if ca[n] != cb[n]))
            except SyntaxError as se:
                be, detail = False, 'SYNTAX-ERR ' + se.msg[:40]
            prod_lines = [l for l in ta.decode('utf-8').splitlines()
                          if l.strip() and not l.startswith('#')]
            results.append((name, 'EFFICACY' if name in EFFICACY else 'CONTROL',
                            'TEXT-SAME' if same else 'TEXT-DIFF',
                            'BYTE-EQUAL' if be else 'DIFF', detail, prod_lines[:6]))
    finally:
        if swapped:
            open(GEN, 'w', encoding='utf-8').write(cur_gen)
            open(ANA, 'w', encoding='utf-8').write(cur_ana)
        assert open(GEN, encoding='utf-8').read() == cur_gen
        assert open(ANA, encoding='utf-8').read() == cur_ana

    eff = [r for r in results if r[1] == 'EFFICACY']
    ctl = [r for r in results if r[1] == 'CONTROL']
    print('==== 功效案 EFFICACY (%d) ====' % len(eff))
    for name, g, s, f, d, pl in eff:
        print('%-20s %-10s %-11s %s' % (name, s, f, d))
        for l in pl:
            print('      | ' + l)
    print('==== 控制案 CONTROL (%d) ====' % len(ctl))
    for name, g, s, f, d, pl in ctl:
        print('%-20s %-10s %-11s %s' % (name, s, f, d))
    n_eq = sum(1 for r in results if r[3] == 'BYTE-EQUAL')
    n_eff_diff = sum(1 for r in eff if r[2] == 'TEXT-DIFF')
    n_ctl_same = sum(1 for r in ctl if r[2] == 'TEXT-SAME')
    n_ctl_eq = sum(1 for r in ctl if r[3] == 'BYTE-EQUAL')
    print()
    print('ALL: %d 案, BYTE-EQUAL %d/%d' % (len(results), n_eq, len(results)))
    print('EFFICACY: %d 案, TEXT-DIFF %d/%d, BYTE-EQUAL %d/%d'
          % (len(eff), n_eff_diff, len(eff),
             sum(1 for r in eff if r[3] == 'BYTE-EQUAL'), len(eff)))
    print('CONTROL: %d 案, A/B TEXT-SAME %d/%d, BYTE-EQUAL %d/%d'
          % (len(ctl), n_ctl_same, len(ctl), n_ctl_eq, len(ctl)))
    json.dump({
        'round': 'rr-v5r112', 'tag': 'v112-NOTBOOL',
        'cases': [{'name': n, 'group': g, 'ab': s, 'recompile': f, 'detail': d}
                  for n, g, s, f, d, _ in results],
        'matrix': {'n': len(results), 'all_byte_equal': n_eq == len(results),
                   'byte_equal': n_eq, 'efficacy_n': len(eff),
                   'efficacy_text_diff': n_eff_diff,
                   'efficacy_byte_equal': sum(1 for r in eff if r[3] == 'BYTE-EQUAL'),
                   'control_n': len(ctl), 'control_text_same': n_ctl_same,
                   'control_byte_equal': n_ctl_eq},
    }, open(EV + '/matrix_v5r112_result.json', 'w', encoding='utf-8'),
        ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
