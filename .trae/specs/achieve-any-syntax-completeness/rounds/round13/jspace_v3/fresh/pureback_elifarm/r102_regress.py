# rr-v5r102 regression driver: for each prior-round repro/variant source:
#   compile -> pyc -> decompile with CURRENT (v101) generator and with HEAD
#   (v101) generator via file swap -> compare product texts byte-wise.
# Also per-top-level-function recompile compare (source vs v101 product).
import os, sys, subprocess, shutil, types, py_compile

REPO = 'F:/Downloads/pythoncdc-main'
R98 = 'D:/temp/opencode/cl_layout/r98'
BASE = REPO + '/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh'
GEN = REPO + '/core/cfg/region_ast_generator.py'

CASES = [
    ('fn_find_new',  BASE + '/useargs_enum/fn_find_new.py'),
    ('te1',          BASE + '/useargs_enum/te1.py'),
    ('mk_iterencode',BASE + '/yp_yieldpre/mk_iterencode.py'),
    ('yp1', BASE + '/yp_yieldpre/yp1.py'),
    ('yp2', BASE + '/yp_yieldpre/yp2.py'),
    ('yp3', BASE + '/yp_yieldpre/yp3.py'),
    ('yp4', BASE + '/yp_yieldpre/yp4.py'),
    ('yp5', BASE + '/yp_yieldpre/yp5.py'),
    ('yp6', BASE + '/yp_yieldpre/yp6.py'),
    ('yp7', BASE + '/yp_yieldpre/yp7.py'),
    ('yp8', BASE + '/yp_yieldpre/yp8.py'),
    ('er1_c3merge',  BASE + '/er_earlyret/er1_c3merge.py'),
    ('er2_plainguard', BASE + '/er_earlyret/er2_plainguard.py'),
    ('er3_guardsimple', BASE + '/er_earlyret/er3_guardsimple.py'),
    ('er4_guardappend', BASE + '/er_earlyret/er4_guardappend.py'),
    ('er_variants',  BASE + '/er_earlyret/er_variants.py'),
    ('fe1_repro',    BASE + '/fe_loopexit/fe1_repro.py'),
    ('fe_variants',  BASE + '/fe_loopexit/fe_variants.py'),
    ('s3_tryelse_loop', BASE + '/te_backedge/s3_tryelse_loop.py'),
    ('te_shapes',    BASE + '/te_backedge/te_shapes.py'),
    ('te_variants8', BASE + '/te_backedge/te_variants8.py'),
    ('w28_shapes',   BASE + '/te_backedge/w28_shapes.py'),
    ('fdt',          R98 + '/fdt.py'),
]
import glob as _glob
for _p in sorted([p for p in _glob.glob(R98 + '/pb[0-9]*.py') + _glob.glob(R98 + '/pv[0-9]*.py') + _glob.glob(R98 + '/pc[0-9]*.py') + _glob.glob(R98 + '/pm[0-9]*.py') if '_out' not in p]):
    CASES.append((_p.replace(chr(92), '/').split('/')[-1][:-3], _p))


def norm(c):
    return (c.co_code.hex(), c.co_exceptiontable.hex(),
            c.co_names, c.co_varnames, c.co_freevars, c.co_cellvars,
            tuple(norm(k) if isinstance(k, types.CodeType) else k for k in c.co_consts))

def toplevels(c):
    out = {}
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            out[k.co_name] = norm(k)
    return out

def decompile(pyc_path, tag):
    outp = R98 + f'/regress_out_{tag}.py'
    errp = R98 + f'/regress_err_{tag}.txt'
    with open(outp, 'wb') as fo, open(errp, 'wb') as fe:
        r = subprocess.run([sys.executable, '-I', '-X', 'utf8', REPO + '/pycdc.py', pyc_path],
                           stdout=fo, stderr=fe, cwd=REPO, timeout=120)
    return open(outp, 'rb').read(), open(errp, 'r', encoding='utf-8', errors='replace').read(), r.returncode

def main():
    head_src = subprocess.run(['E:/Program Files/PortableGit/bin/git.exe', '-C', REPO,
                               'show', 'HEAD:core/cfg/region_ast_generator.py'],
                              capture_output=True).stdout.decode('utf-8')
    head_src2 = subprocess.run(['E:/Program Files/PortableGit/bin/git.exe', '-C', REPO,
                               'show', 'HEAD:core/cfg/region_analyzer.py'],
                              capture_output=True).stdout.decode('utf-8')
    cur = open(GEN, encoding='utf-8').read()
    ANAGEN = REPO + '/core/cfg/region_analyzer.py'
    curana = open(ANAGEN, encoding='utf-8').read()
    assert 'v102-PUREBACK' in open('F:/Downloads/pythoncdc-main/core/cfg/region_analyzer.py', encoding='utf-8').read(), 'current analyzer missing v102 patch'
    assert 'v102-PUREBACK' not in head_src2, 'HEAD already contains v102 patch?'
    os.makedirs(R98 + '/regress_v102', exist_ok=True)
    os.makedirs(R98 + '/regress_v102base', exist_ok=True)
    swapped = False
    try:
        results = []
        for name, src in CASES:
            pyc = R98 + f'/regress_{name}.pyc'
            py_compile.compile(src, cfile=pyc, doraise=True)
            t98, e98, rc98 = decompile(pyc, name + '_v102')
            (R98 + f'/regress_v102/{name}.py').encode()
            open(R98 + f'/regress_v102/{name}.py', 'wb').write(t98)
            open(GEN, 'w', encoding='utf-8').write(head_src)
            open(ANAGEN, 'w', encoding='utf-8').write(head_src2)
            swapped = True
            t97, e97, rc97 = decompile(pyc, name + '_v101base')
            open(R98 + f'/regress_v102base/{name}.py', 'wb').write(t97)
            open(GEN, 'w', encoding='utf-8').write(cur)
            open(ANAGEN, 'w', encoding='utf-8').write(curana)
            swapped = False
            same = (t98 == t97)
            # per-top-level-fn compare source vs v98 product
            fn_status = 'COMPILE-FAIL'
            try:
                prod = compile(t98.decode('utf-8'), 'p', 'exec')
                srcc = compile(open(src, encoding='utf-8').read(), 's', 'exec')
                ts, tp = toplevels(srcc), toplevels(prod)
                removed = sorted(set(ts) - set(tp)); added = sorted(set(tp) - set(ts))
                changed = sorted(n for n in set(ts) & set(tp) if ts[n] != tp[n])
                if not removed and not added and not changed:
                    fn_status = 'BYTE-EQUAL'
                else:
                    fn_status = f'DIFF rem={removed} add={added} chg={changed}'
            except SyntaxError as se:
                fn_status = f'SYNTAX-ERR {se.msg[:40]}'
            results.append((name, 'TEXT-SAME' if same else 'TEXT-DIFF', fn_status,
                            (e98 or '').strip().splitlines()[:1]))
        print()
        for name, s, f, e in results:
            print(f'{name:18s} {s:10s} {f}')
        nd = sum(1 for _, s, _, _ in results if s == 'TEXT-DIFF')
        print()
        print('TEXT-DIFF count:', nd, '/', len(results))
    finally:
        if swapped:
            open(GEN, 'w', encoding='utf-8').write(cur)
            open(ANAGEN, 'w', encoding='utf-8').write(curana)
        assert open(GEN, encoding='utf-8').read() == cur, 'generator not restored!'
        assert open(ANAGEN, encoding='utf-8').read() == curana, 'analyzer not restored!'

if __name__ == '__main__':
    main()
