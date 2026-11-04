# rr-v5r113 [v113-WYBREAK] 复现矩阵（15 案）
#   compile -> pyc -> pycdc(current v113) -> recompile -> 全 code object 逐字段
#   BYTE-EQUAL；并与 HEAD d742d4d0 版 A/B 文件交换逐案比产品文本。
#   中间产物写 D:/temp/opencode/cl_layout/r113matrix（不落证据目录）。
import os, sys, subprocess, types, py_compile, marshal, json

REPO = 'F:/Downloads/pythoncdc-main'
EV = REPO + '/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/whileyield_break'
MP = 'D:/temp/opencode/cl_layout/r113matrix'
GEN = REPO + '/core/cfg/region_ast_generator.py'
ANA = REPO + '/core/cfg/region_analyzer.py'
PY = 'D:/Python/python.exe'
HEAD = 'd742d4d0'

# 目标形态（while + yield + 尾部 break 的生成器）：修复前由 _ii NameError
# 触发逐块降级，产品丢 while/yield/break；修复后应 BYTE-EQUAL 且 A/B TEXT-DIFF。
EFFICACY = {
 'r1_while_yield_break': """def g(first_int, last_int):
    while first_int <= last_int:
        yield first_int
        first_int += 1
        if first_int > last_int:
            break
""",
 'r2_while_yield_preinit': """def g(first, last):
    ip_bits = first.bits
    first_int = first.val
    last_int = last.val
    while first_int <= last_int:
        nbits = min(first_int, ip_bits)
        net = (first_int, ip_bits - nbits)
        yield net
        first_int += 1 << nbits
        if first_int - 1 == 255:
            break
""",
 'r4_exact_shape': """def summarize(first, last):
    ip_bits = first._max_prefixlen
    first_int = first._ip
    last_int = last._ip
    while first_int <= last_int:
        nbits = min(_count_righthand_zero_bits(first_int, ip_bits), (last_int - first_int + 1).bit_length() - 1)
        net = ip((first_int, ip_bits - nbits))
        yield net
        first_int += 1 << nbits
        if first_int - 1 == ip._ALL_ONES:
            break
""",
 'w1_break_ne': """def g(a, b):
    while a <= b:
        yield a
        a += 1
        if a != b:
            break
""",
 'w2_no_preinit': """def g(a, b):
    while a < b:
        yield a * 2
        a += 2
        if a >= b:
            break
""",
 'w3_multi_yield': """def g(a, b):
    while a <= b:
        yield a
        yield a + 1
        a += 1
        if a > b:
            break
""",
 'w4_break_const': """def g(a):
    while a >= 0:
        yield a
        a -= 1
        if a == 10:
            break
""",
 'w5_break_attr': """def g(first, last, ip):
    bits = first._max_prefixlen
    cur = first._ip
    end = last._ip
    while cur <= end:
        net = ip((cur, bits))
        yield net
        cur += 1
        if cur - 1 == ip._ALL_ONES:
            break
""",
 'w6_calc_body': """def g(a, b):
    total = 0
    while a <= b:
        total = total + a
        yield total
        a += 1
        if a * 2 > b:
            break
""",
}

# 控制/相邻形态：非目标形态 A/B 产品文本须逐字节 TEXT-SAME。
CONTROL = {
 'r3_while_yield_no_break': """def g(first_int, last_int):
    while first_int <= last_int:
        yield first_int
        first_int += 1
""",
 'c1_while_break_no_yield': """def g(a, b):
    while a < b:
        a += 1
        if a > b:
            break
    return a
""",
 'c2_while_yield_continue': """def g(a, b):
    while a <= b:
        yield a
        a += 1
        if a > b:
            continue
""",
 'c3_plain_while': """def g(a, b):
    s = 0
    while a <= b:
        s += a
        a += 1
    return s
""",
 'c4_while_true_break': """def g(a):
    while True:
        a -= 1
        if a < 0:
            break
    return a
""",
 'c5_break_mid': """def g(a, b):
    while a <= b:
        if a == 5:
            break
        yield a
        a += 1
""",
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
    import subprocess as sp
    head_gen = sp.run(['git', '-C', REPO, 'show', HEAD + ':core/cfg/region_ast_generator.py'],
                      capture_output=True).stdout.decode('utf-8')
    head_ana = sp.run(['git', '-C', REPO, 'show', HEAD + ':core/cfg/region_analyzer.py'],
                      capture_output=True).stdout.decode('utf-8')
    assert 'v113-WYBREAK' not in head_gen
    cur_gen = open(GEN, encoding='utf-8').read()
    cur_ana = open(ANA, encoding='utf-8').read()
    assert 'v113-WYBREAK' in cur_gen, 'current GEN missing v113 patch'
    assert 'v112-NOTBOOL' in head_gen, 'HEAD should contain v112 patch'
    os.makedirs(MP, exist_ok=True)
    results = []
    swapped = False
    try:
        for name, src in CASES.items():
            sp_py = MP + '/%s.py' % name
            pyc = MP + '/%s.pyc' % name
            pa = MP + '/%s_v113.py' % name
            pb = MP + '/%s_head.py' % name
            open(sp_py, 'w', encoding='utf-8').write(src)
            py_compile.compile(sp_py, pyc, doraise=True)
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

            def check(text):
                try:
                    cb = {n: norm(c) for n, c in flat(compile(text.decode('utf-8'), 'p', 'exec')).items()}
                    be = (ca == cb)
                    detail = '' if be else 'rem=%s add=%s chg=%s' % (
                        sorted(set(ca) - set(cb)), sorted(set(cb) - set(ca)),
                        sorted(n for n in set(ca) & set(cb) if ca[n] != cb[n]))
                except SyntaxError as se:
                    be, detail = False, 'SYNTAX-ERR ' + se.msg[:40]
                return be, detail

            be, detail = check(ta)
            hbe, _ = check(tb)
            prod_lines = [l for l in ta.decode('utf-8').splitlines()
                          if l.strip() and not l.startswith('#')]
            results.append((name, 'EFFICACY' if name in EFFICACY else 'CONTROL',
                            'TEXT-SAME' if same else 'TEXT-DIFF',
                            'BYTE-EQUAL' if be else 'DIFF',
                            'BYTE-EQUAL' if hbe else 'DIFF', detail, prod_lines[:8]))
    finally:
        if swapped:
            open(GEN, 'w', encoding='utf-8').write(cur_gen)
            open(ANA, 'w', encoding='utf-8').write(cur_ana)
        assert open(GEN, encoding='utf-8').read() == cur_gen
        assert open(ANA, encoding='utf-8').read() == cur_ana

    eff = [r for r in results if r[1] == 'EFFICACY']
    ctl = [r for r in results if r[1] == 'CONTROL']
    print('==== 功效案 EFFICACY (%d) ====' % len(eff))
    for name, g, s, f, hf, d, pl in eff:
        print('%-24s %-10s v113=%-11s HEAD=%-11s %s' % (name, s, f, hf, d))
        for l in pl:
            print('      | ' + l)
    print('==== 控制案 CONTROL (%d) ====' % len(ctl))
    for name, g, s, f, hf, d, pl in ctl:
        print('%-24s %-10s v113=%-11s HEAD=%-11s %s' % (name, s, f, hf, d))
    n_eq = sum(1 for r in results if r[3] == 'BYTE-EQUAL')
    n_eff_diff = sum(1 for r in eff if r[2] == 'TEXT-DIFF')
    n_ctl_same = sum(1 for r in ctl if r[2] == 'TEXT-SAME')
    n_ctl_eq = sum(1 for r in ctl if r[3] == 'BYTE-EQUAL')
    print()
    print('ALL: %d 案, v113 BYTE-EQUAL %d/%d' % (len(results), n_eq, len(results)))
    print('EFFICACY: %d 案, TEXT-DIFF %d/%d, v113 BYTE-EQUAL %d/%d'
          % (len(eff), n_eff_diff, len(eff),
             sum(1 for r in eff if r[3] == 'BYTE-EQUAL'), len(eff)))
    print('CONTROL: %d 案, A/B TEXT-SAME %d/%d, v113 BYTE-EQUAL %d/%d'
          % (len(ctl), n_ctl_same, len(ctl), n_ctl_eq, len(ctl)))
    json.dump({
        'round': 'rr-v5r113', 'tag': 'v113-WYBREAK',
        'cases': [{'name': n, 'group': g, 'ab': s, 'recompile_v113': f,
                   'recompile_HEAD': hf, 'detail': d}
                  for n, g, s, f, hf, d, _ in results],
        'matrix': {'n': len(results), 'all_byte_equal': n_eq == len(results),
                   'byte_equal': n_eq, 'efficacy_n': len(eff),
                   'efficacy_text_diff': n_eff_diff,
                   'efficacy_byte_equal': sum(1 for r in eff if r[3] == 'BYTE-EQUAL'),
                   'control_n': len(ctl), 'control_text_same': n_ctl_same,
                   'control_byte_equal': n_ctl_eq},
    }, open(EV + '/matrix_v5r113_result.json', 'w', encoding='utf-8'),
        ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
