"""Round-1 shape search: enumerate candidate constructs around a defect signature.

Writes candidates under test_repros/round1/_search/, compiles, decompiles with pycdc.py
and judges each with scripts/pyc_verify.py single (the only criterion).
Usage: python -X utf8 test_repros/round1/_search.py <template-name|all> [max]
"""
import os
import py_compile
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, '_search')
PY = sys.executable


def run(cmd, timeout=200):
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                      errors='replace', timeout=timeout)
    return (p.stdout or '') + (p.stderr or '')


def judge(apy):
    base = apy[:-3]
    try:
        py_compile.compile(apy, base + '.pyc', doraise=True)
    except Exception as exc:  # noqa: BLE001
        return 'COMPILE_FAIL', str(exc)[:120]
    out = run([PY, '-X', 'utf8', 'pycdc.py', '-o', base + 'OK.py', base + '.pyc'])
    if not os.path.isfile(base + 'OK.py'):
        return 'DECOMPILE_FAIL', out[-160:]
    txt = run([PY, '-X', 'utf8', 'scripts/pyc_verify.py', 'single', base + '.pyc'])
    if 'status=failure' in txt:
        units = [ln.strip() for ln in txt.splitlines() if ln.startswith('***')]
        return 'MISMATCH', ';'.join(units)[:180]
    if 'status=success' in txt:
        return 'MATCH', ''
    return 'ERROR', txt[-160:]


# ── candidate space around the cgroup_utils `set_cgroup_config` signature ──
GUARD = "        if get_flag(x) is None:\n            log('none')\n            return None\n"
BLOCK = ("        if k1 == 1:\n"
         "            if k2 == 1:\n"
         "                log('in')\n"
         "            else:\n"
         "                log('out')\n"
         "            log('tail')\n"
         "        else:\n"
         "            other(x, 'a')\n")
BLOCK_PLAIN = ("        if k1 == 1:\n"
               "            log('yes')\n"
               "        else:\n"
               "            other(x, 'a')\n")
BLOCK_NOELSE = ("        if k1 == 1:\n"
                "            log('yes')\n")
NEST2 = ("        if k1 == 1:\n"
         "            if k2 == 1:\n"
         "                if k3 == 1:\n"
         "                    log('d3')\n"
         "                else:\n"
         "                    log('d3e')\n"
         "            else:\n"
         "                log('d2e')\n"
         "        else:\n"
         "            other(x, 'a')\n")


def head():
    return ("def log(m):\n    print(m)\n\n\n"
            "def other(u, v):\n    print(u, v)\n\n\n"
            "def get_flag(u):\n    return u\n\n\n")


def make(name, body):
    return os.path.join(OUT, f'{name}.py'), head() + body


CANDS = {}


def add(name, body):
    CANDS[name] = body


for nblocks in (1, 2, 3):
    for guard in (False, True):
        for hret in (False, True):
            body = 'def f(x):\n    try:\n'
            if guard:
                body += GUARD
            body += BLOCK * nblocks
            body += '    except BaseException:\n        log(\'err\')\n'
            body += '        return None\n' if hret else ''
            add(f'b{nblocks}_g{int(guard)}_h{int(hret)}', body)

# no try at all
add('notry_2blk', 'def f(x):\n' + (BLOCK * 2))
# bare except / except as
add('bareexcept_hret', 'def f(x):\n    try:\n' + GUARD + BLOCK * 2 +
    "    except BaseException as e:\n        log('err')\n        return None\n")
# last block without else
add('lastnoe', 'def f(x):\n    try:\n' + GUARD + BLOCK + BLOCK_PLAIN + BLOCK_NOELSE +
    "    except BaseException:\n        log('err')\n        return None\n")
# last block plain (no nested)
add('lastplain', 'def f(x):\n    try:\n' + GUARD + BLOCK + BLOCK_PLAIN +
    "    except BaseException:\n        log('err')\n        return None\n")
# depth-3 nesting only
add('nest3_hret', 'def f(x):\n    try:\n' + GUARD + NEST2 +
    "    except BaseException:\n        log('err')\n        return None\n")
# try inside try, handler return None
add('tryintry', 'def f(x):\n    try:\n' + GUARD + '        try:\n' + BLOCK.replace('        ', '            ') +
    "        except BaseException:\n            log('inner')\n"
    "    except BaseException:\n        log('err')\n        return None\n")
# handler with if/else + return
add('handler_ifelse', 'def f(x):\n    try:\n' + GUARD + BLOCK * 2 +
    "    except BaseException:\n        if x == 1:\n            log('e1')\n"
    "        else:\n            other(x, 'e2')\n        return None\n")
# module-body host
add('module_host', 'try:\n' + GUARD.replace('        ', '    ') + BLOCK.replace('        ', '    ') +
    "except BaseException:\n    log('err')\n")

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    pat = sys.argv[1] if len(sys.argv) > 1 else 'all'
    names = [n for n in CANDS if pat == 'all' or pat in n]
    for n in names:
        path, src = make(n, CANDS[n])
        with open(path, 'w', encoding='utf-8') as f:
            f.write(src)
        verdict, info = judge(path)
        print(f'{n:<28} {verdict:<9} {info}')
