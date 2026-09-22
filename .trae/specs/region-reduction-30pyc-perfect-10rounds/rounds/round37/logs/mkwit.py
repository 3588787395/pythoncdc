# -*- coding: utf-8 -*-
"""Round 37 witness battery (orchestrator-side).

Shapes are reductions of strategy.pyc :: tick_worker_thread's missing elif arm:
a nested if/elif chain whose arms are `or` of two chained comparisons, sitting in
an arm of an ANCESTOR if/elif chain, inside a `while True:` whose other arms end in
`continue`.  W* are witnesses (must FAIL on landed bytes), C* are controls (must PASS).

  python -X utf8 mkwit.py        # writes wit/*.py, compiles each to check syntax
"""
import io
import os
import sys

OUT = r'D:/Temp/r37gate/r37/wit'
PRE = ('# -*- coding: utf-8 -*-\n'
       '"""r37 battery case"""\n'
       'from time import sleep\n'
       '\n'
       '\n'
       'def s(n):\n'
       '    return n\n'
       '\n'
       '\n'
       'def ok():\n'
       '    return True\n'
       '\n'
       '\n'
       'def f(x):\n'
       '    return x\n'
       '\n'
       '\n')

# nested or-of-chained-comparisons chain, indented for "inside `if dt == 'a':` at 8"
NEST2 = """            if '08:30' <= dt < '08:59' or '12:30' <= dt < '12:59':
                s(60)
            elif '08:59' <= dt < '09:00' or '12:59' <= dt < '13:00':
                s(5)
"""
NEST2_ELSE = """            if '08:30' <= dt < '08:59' or '12:30' <= dt < '12:59':
                s(60)
            elif '08:59' <= dt < '09:00' or '12:59' <= dt < '13:00':
                s(5)
            elif not (dt > '15:00' or dt < '09:00'):
                if '09:00' <= dt < '09:29' or '12:30' <= dt < '12:59':
                    s(60)
                elif '09:29' <= dt < '09:30' or '12:59' <= dt < '13:00':
                    s(5)
                else:
                    continue
"""
HEAD = """    while True:
        if not ok():
            sleep(60)
            continue
"""

CASES = {
    # W1: ancestor if/elif + loop + 2-arm nested or-chain
    'w1_loop_ancestor_2arms': """def tick(dt):
""" + HEAD + """        if dt == 'a':
""" + NEST2 + """        elif f(dt):
            pass
    return None
""",
    # W2: as W1 but the nested chain carries the extra `elif not (...)` arm with
    # its own nested chain that ends in `continue` (the real tick_worker_thread shape)
    'w2_loop_ancestor_withelse_continue': """def tick(dt):
""" + HEAD + """        if dt == 'a':
""" + NEST2_ELSE + """        elif f(dt):
            pass
    return None
""",
    # W3: three or-arms in the nested chain, ancestor elif present, inside the loop
    'w3_loop_ancestor_3arms': """def tick(dt):
""" + HEAD + """        if dt == 'a':
            if '08:30' <= dt < '08:59' or '12:30' <= dt < '12:59':
                s(60)
            elif '08:59' <= dt < '09:00' or '12:59' <= dt < '13:00':
                s(5)
            elif '09:00' <= dt < '09:29' or '13:00' <= dt < '14:00':
                s(60)
        elif f(dt):
            pass
    return None
""",
    # C1: control = W1 without the ancestor `elif` (nothing to lend)
    'c1_loop_no_ancestor_elif': """def tick(dt):
""" + HEAD + """        if dt == 'a':
""" + NEST2 + """    return None
""",
    # C2: control = W1 without the loop (ancestor elif present, arms fall through)
    'c2_no_loop_ancestor_2arms': """def tick(dt):
    if dt == 'a':
""" + NEST2 + """    elif f(dt):
        pass
    return None
""",
    # C3: control = loop + ancestor elif but the nested chain is plain (no `or`)
    'c3_loop_ancestor_plain_chain': """def tick(dt):
""" + HEAD + """        if dt == 'a':
            if '08:30' <= dt < '08:59':
                s(60)
            elif '08:59' <= dt < '09:00':
                s(5)
            else:
                continue
        elif f(dt):
            pass
    return None
""",
    # C4: control = single or-arm nested in an ancestor elif chain, inside the loop
    'c4_loop_ancestor_single_arm': """def tick(dt):
""" + HEAD + """        if dt == 'a':
            if '08:30' <= dt < '08:59' or '12:30' <= dt < '12:59':
                s(60)
        elif f(dt):
            pass
    return None
""",
}

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for k, v in sorted(CASES.items()):
        src = PRE + v
        compile(src, k, 'exec')
        io.open(os.path.join(OUT, k + '.py'), 'w', encoding='utf-8', newline='\n').write(src)
        print('wrote', k, len(v.splitlines()), 'lines')
