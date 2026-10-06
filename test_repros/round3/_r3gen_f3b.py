"""Round-3 extra arms pinning B112's claim condition (elif-chain arm + mixed is-None or-chain
shared then-arm sink). Same pipeline; judge = scripts/pyc_verify.py."""
import json
import pathlib
import py_compile
import subprocess
import sys

ROOT = pathlib.Path(r'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main')
D = ROOT / 'test_repros' / 'round3'

A = r'''
def f(t, sv, lv):
    if t == 'a':
        return 1
    elif t == 'b':
        if sv is None or lv is None:
            return None
        return down(sv, lv)
'''
B = r'''
def f(t, sv, lv):
    if t == 'a':
        return 1
    elif t == 'b':
        if sv is None or lv is None:
            return None
        return down(sv[-1], lv[-1])
    return None
'''
C = r'''
def f(t, sv, lv):
    if t == 'a':
        return 1
    elif t == 'b':
        if sv is None:
            return None
        return down(sv[-1], lv[-1])
    return None
'''
E = r'''
def f(t, sv, lv):
    if t == 'a':
        if sv is None or lv is None:
            return None
        return down(sv[-1], lv[-1])
    return None
'''
G = r'''
def f(t, sv, lv):
    if t == 'a':
        return 1
    elif t == 'b':
        if sv is None or lv is None:
            return 0
        return down(sv[-1], lv[-1])
    return None
'''
H = r'''
def f(t, sv, lv):
    if t == 'a':
        return 1
    elif t == 'b':
        if sv is None or lv is None or t is None:
            return None
        return down(sv[-1], lv[-1])
    return None
'''

ARMS = {
    'r3_c17_elifchain_no_trailing_return': A,
    'r3_c18_elifchain_plain_args': B,
    'r3_c19_elifchain_single_member_chain': C,
    'r3_c20_ifarm_not_elif_chain': E,
    'r3_c21_elifchain_then_returns_const': G,
    'r3_c22_elifchain_three_members': H,
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
merged = sorted(set(seen) | {f'test_repros/round3/{x}.pyc' for x in names})
f.write_text(json.dumps([{'path': x} for x in merged], indent=2), encoding='utf-8')
print('built', len(names), 'index', len(merged))
