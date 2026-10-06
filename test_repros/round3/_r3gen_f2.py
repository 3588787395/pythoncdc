"""Round-3 file-2 specimens (klinedata.pyc): B110 mixed jump-family boolop chain,
B111 loop/region exit vs function-tail terminal join, B112 `not X and ...` chain join.
Same three-step pipeline as _r3gen.py. Judge = scripts/pyc_verify.py only.
"""
import json
import pathlib
import py_compile
import subprocess
import sys

ROOT = pathlib.Path(r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main')
D = ROOT / 'test_repros' / 'round3'

B1 = r'''
def f(fq, div, fields):
    if fq is None or not div or isinstance(fields, str) and 'x' in fields:
        need = 0
    else:
        need = 1
    for t in TYPES:
        use(need, t)
    return need
'''
B2 = r'''
def f(fq, div, fields):
    if fq is None or not div or isinstance(fields, str) and 'x' in fields:
        need = 0
    else:
        need = 1
    use(need)
    return need
'''
B3 = r'''
def f(a, b, c, d):
    if a or not b or isinstance(c, str) and d:
        need = 0
    else:
        need = 1
    for t in TYPES:
        use(need, t)
    return need
'''
B4 = r'''
def f(a, b, c, d):
    if a and b or c and d:
        need = 0
    else:
        need = 1
    for t in TYPES:
        use(need, t)
    return need
'''
B5 = r'''
def f(fq, div):
    if fq is None or not div:
        need = 0
    else:
        need = 1
    for t in TYPES:
        use(need, t)
    return need
'''
B6 = r'''
class C:
    def m(self, fq, div, fields):
        if fq is None or not div or isinstance(fields, str) and 'x' in fields:
            need = 0
        else:
            need = 1
        for t in TYPES:
            use(need, t)
        return need
'''
B7 = r'''
def f(fq, div, fields):
    if fq is None or not div or isinstance(fields, str) and 'x' in fields:
        need = 0
    else:
        need = 1
    return need
'''
L1 = r'''
def f(a, syms, x):
    res = None
    if a:
        res = mk(1)
    for s in syms:
        if s:
            res = mk(2)
            break
        use(s)
    return res
'''
L2 = r'''
def f(a, syms, x):
    if a:
        res = mk(1)
    else:
        for s in syms:
            use(s)
            if s > 1:
                break
        else:
            res = mk(x)
    return res
'''
L3 = r'''
def f(cond, syms, x):
    if cond:
        for s in syms:
            use(s)
            break
    else:
        x = mk(1)
    return x
'''
L4 = r'''
def f(cond, syms, x):
    for s in syms:
        if cond:
            break
        use(s)
    else:
        x = mk(1)
    return x
'''
L5 = r'''
def f(cond, syms, x):
    if cond:
        for s in syms:
            if s:
                break
            use(s)
    else:
        x = mk(1)
    return x
'''
K1 = r'''
def f(include, freq, qd, am, pm, ac, pc):
    if not include and freq == 1 and qd not in (am, pm) and (qd > ac or qd > pc):
        out = step(qd)
    out2 = tail(qd)
    if include:
        return 7
    return out2
'''
K2 = r'''
def f(include, freq, qd, am, pm, ac, pc):
    if not include and freq == 1 and qd not in (am, pm):
        out = step(qd)
    out2 = tail(qd)
    return out2
'''
K3 = r'''
def f(include, freq, qd):
    if include and freq == 1:
        out = step(qd)
    out2 = tail(qd)
    return out2
'''

ARMS = {
    'r3_b01_mixedjump_chain_then_skipped': B1,
    'r3_b02_mixedjump_chain_no_loop': B2,
    'r3_b03_alliffalse_family_chain': B3,
    'r3_b04_andor_family_chain': B4,
    'r3_b05_isnone_not_only_two_members': B5,
    'r3_b06_mixedjump_method_host': B6,
    'r3_b07_mixedjump_chain_return_join': B7,
    'r3_b08_loopexit_break_before_tailreturn': L1,
    'r3_b09_loopexit_in_elsearm_for_else': L2,
    'r3_b10_loopexit_arm_sibling_elsebranch': L3,
    'r3_b11_for_else_tail_join': L4,
    'r3_b12_loopexit_in_ifarm_elsebranch': L5,
    'r3_b13_notx_andchain_join_absorbed': K1,
    'r3_b14_notx_andchain_short': K2,
    'r3_b15_positive_andchain': K3,
}

names = sys.argv[1:] or sorted(ARMS)
for n in names:
    p = D / (n + '.py')
    p.write_text(ARMS[n].lstrip('\n'), encoding='utf-8')
    py_compile.compile(str(p), cfile=str(D / (n + '.pyc')), doraise=True, quiet=1)
    ok = D / (n + 'OK.py')
    if ok.exists():
        ok.unlink()
    r = subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', '-o', str(ok),
                        str(D / (n + '.pyc'))], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print('DECOMPILE_FAIL', n, r.stderr[-200:])

f = D / 'r3_probe_index.json'
seen = [e['path'] for e in json.loads(f.read_text(encoding='utf-8'))] if f.exists() else []
merged = sorted(set(seen) | {f'test_repros/round3/{n}.pyc' for n in names})
f.write_text(json.dumps([{'path': x} for x in merged], indent=2), encoding='utf-8')
print('built', len(names), 'arms; index size', len(merged))
