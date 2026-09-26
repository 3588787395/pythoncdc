# -*- coding: utf-8 -*-
"""Minimal synthetic repros: if/elif chains whose branches return a comprehension.

  python -X utf8 synth/mk_repro.py            # build + decompile + report duplicates
  python -X utf8 synth/mk_repro.py --keep     # also keep the .py/.pyc files
"""
import io
import os
import py_compile
import sys
import textwrap

REPO = r'F:/Downloads/pythoncdc-main'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

CASES = {}

CASES['chain3_lc'] = '''
def f(x, orders):
    if x is None:
        return [o for o in orders]
    elif isinstance(x, int):
        return [o for o in orders if o == x]
    elif isinstance(x, str):
        return [o for o in orders if o == x]
    else:
        return []
'''

CASES['chain3_plain'] = '''
def f(x, orders):
    if x is None:
        return orders
    elif isinstance(x, int):
        return orders
    elif isinstance(x, str):
        return orders
    else:
        return None
'''

CASES['if_else_lc'] = '''
def f(x, orders):
    if x is None:
        return [o for o in orders]
    else:
        return [o for o in orders if o == x]
'''

CASES['chain_mixed'] = '''
def f(x, orders):
    if x is None:
        return orders
    elif isinstance(x, int):
        y = x
        return [o for o in orders if o == y]
    else:
        return []
'''

CASES['chain_last_lc'] = '''
def f(x, orders):
    if x is None:
        return orders
    elif isinstance(x, int):
        return orders
    else:
        return [o for o in orders]
'''

CASES['chain_noelse_lc'] = '''
def f(x, orders):
    if x is None:
        return [o for o in orders]
    elif isinstance(x, int):
        return [o for o in orders if o == x]
    return []
'''

CASES['if_only_lc'] = '''
def f(x, orders):
    if x is None:
        return [o for o in orders]
    return []
'''


def count_returns(src, marker):
    return src.count(marker)


def main():
    import pycdc
    keep = '--keep' in sys.argv
    lines = []
    for name, body in CASES.items():
        code = textwrap.dedent(body).lstrip()
        py = os.path.join(HERE, name + '.py')
        pyc = py + 'c'
        io.open(py, 'w', encoding='utf-8', newline='\n').write(code)
        py_compile.compile(py, cfile=pyc, doraise=True, optimize=0)
        out = pycdc.decompile_pyc(pyc)
        got = '\n'.join(l for l in out.split('\n')
                        if not l.startswith('# Source') and not l.startswith('# File')).strip('\n')
        dup = []
        ls = got.split('\n')
        for i in range(len(ls) - 1):
            if ls[i].strip() and ls[i].strip() == ls[i + 1].strip():
                dup.append(ls[i].strip())
        lines.append('===== %s  dup-lines=%d %s' % (name, len(dup), dup))
        lines.append(got.rstrip())
        if not keep:
            for f in (py, pyc):
                try:
                    os.remove(f)
                except OSError:
                    pass
    txt = chr(10).join(lines)
    outp = os.path.join(HERE, '..', 'dump', 'synth_repro.txt')
    io.open(outp, 'w', encoding='utf-8', newline='\n').write(txt)
    print(txt)


main()
