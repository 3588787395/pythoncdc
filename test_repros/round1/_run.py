"""Round-1 repro battery harness (test-engineer tooling; judge = scripts/pyc_verify.py only).

Usage:
  python -X utf8 test_repros/round1/_run.py <a.py> [<b.py> ...]
For each .py: compile to sibling .pyc, decompile with pycdc.py to <base>OK.py,
then judge with `python -X utf8 scripts/pyc_verify.py single <base>.pyc`.
"""
import os
import py_compile
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PY = sys.executable


def run(cmd, timeout=280):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=timeout)
    return (p.stdout or '') + (p.stderr or '')


def one(py):
    apy = py if os.path.isabs(py) else os.path.join(ROOT, py)
    base = apy[:-3] if apy.endswith('.py') else apy
    try:
        py_compile.compile(apy, base + '.pyc', doraise=True)
    except Exception as exc:  # noqa: BLE001
        print(f'{os.path.basename(apy)}: COMPILE_FAIL {exc}')
        return
    out = run([PY, '-X', 'utf8', 'pycdc.py', '-o', base + 'OK.py', base + '.pyc'])
    if not os.path.isfile(base + 'OK.py'):
        print(f'{os.path.basename(apy)}: DECOMPILE_FAIL rc-output={out[-300:]}')
        return
    txt = run([PY, '-X', 'utf8', 'scripts/pyc_verify.py', 'single', base + '.pyc'])
    verdict = 'MISMATCH' if 'status=failure' in txt else ('MATCH' if 'status=success' in txt else 'ERROR')
    lines = [ln for ln in txt.splitlines()
             if ln.startswith('***') or 'status=' in ln]
    print(f'{os.path.basename(apy):<46} {verdict:<9} | ' + ' | '.join(ln.strip() for ln in lines))
    if verdict == 'ERROR':
        print(txt[-500:])


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        one(arg)
