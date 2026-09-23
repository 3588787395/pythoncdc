# -*- coding: utf-8 -*-
"""Ground truth: where does CPython 3.11 put the loop back edge around a try/except?"""
import dis
import sys

sys.stdout.reconfigure(encoding='utf-8')

VARIANTS = {
    'T1 try-last': '''
def f(xs):
    for x in xs:
        try:
            a = g(x)
        except:
            h(x)
''',
    'T2 try+continue': '''
def f(xs):
    for x in xs:
        try:
            a = g(x)
        except:
            h(x)
        continue
''',
    'T3 try+stmt': '''
def f(xs):
    for x in xs:
        try:
            a = g(x)
        except:
            h(x)
        k(x)
''',
    'T4 try-last-nested-if': '''
def f(xs):
    for x in xs:
        if x:
            try:
                a = g(x)
            except:
                h(x)
                return 1
            continue
        k(x)
''',
}

for tag, src in VARIANTS.items():
    print('======== %s ========' % tag)
    ns = {}
    exec(compile(src, '<t>', 'exec'), ns)
    dis.dis(ns['f'])
    print()
