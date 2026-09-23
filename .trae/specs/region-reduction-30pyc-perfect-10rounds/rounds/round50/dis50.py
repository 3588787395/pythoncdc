# -*- coding: utf-8 -*-
"""Side-by-side instruction dump for one code object, original pyc vs product pyc.

usage: python -X utf8 dis50.py <orig-pyc> <prod-pyc> <func-name>
"""
import dis
import importlib.util
import io
import sys
import types as _t

REPO = r'F:\Downloads\pythoncdc-main'
OPYC, PPATH, NAME = sys.argv[1], sys.argv[2], sys.argv[3]
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('pc50d', REPO + '/pycdc.py')
pc = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pc)


def walk(co, path=''):
    yield path, co
    for c in co.co_consts:
        if isinstance(c, _t.CodeType):
            yield from walk(c, path + '/' + c.co_name)


def find(pyc, name):
    if pyc.endswith('.py'):
        co = compile(io.open(pyc, encoding='utf-8').read(), pyc, 'exec')
    else:
        mod = pc.load_pyc_file_v2(pyc)
        code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
        if hasattr(code, 'to_python_code'):
            code = code.to_python_code()
        co = code
    for p, c in walk(co):
        if p.endswith('/' + name):
            return c
    return None


def fmt(co):
    out = []
    for i in dis.get_instructions(co):
        out.append((i.offset, i.opname, i.argrepr))
    return out


a, b = fmt(find(OPYC, NAME)), fmt(find(PPATH, NAME))
print('orig=%d decomp=%d' % (len(a), len(b)))
n = max(len(a), len(b))
for k in range(n):
    x = '%-7s %-32s %s' % a[k] if k < len(a) else ''
    y = '%-7s %-32s %s' % b[k] if k < len(b) else ''
    mark = '' if (k < len(a) and k < len(b) and a[k][1] == b[k][1]) else '   <<<'
    print('%-44s | %-44s%s' % (x, y, mark))
