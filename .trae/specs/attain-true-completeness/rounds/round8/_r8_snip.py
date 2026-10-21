# -*- coding: utf-8 -*-
"""R8 probe: compile src snippets, decompile with pycdc, diff bytecode vs original.

Usage: python -X utf8 _r8_snip.py <file.py>
"""
import dis
import marshal
import os
import subprocess
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
os.chdir(ROOT)
OUT = r'd:\Temp\opencode\r8\snip'


def dump(co):
    out = []
    for i in dis.get_instructions(co):
        arg = i.argrepr
        if hasattr(i.argval, 'co_name'):
            arg = 'CODE'
        out.append('%5s %-28s %s' % (i.offset, i.opname, arg))
    return out


def all_codes(co, prefix=''):
    res = [(prefix + co.co_name, co)]
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            res.extend(all_codes(c, prefix + co.co_name + '.'))
    return res


src_path = sys.argv[1]
name = os.path.basename(src_path).replace('.py', '')
os.makedirs(OUT, exist_ok=True)
src = open(src_path, encoding='utf-8').read()
code = compile(src, name + '.py', 'exec')
pyc = os.path.join(OUT, name + '.pyc')
import importlib.util
with open(pyc, 'wb') as f:
    f.write(importlib.util.MAGIC_NUMBER)
    f.write(b'\x00' * 12)
    f.write(marshal.dumps(code))

prod = os.path.join(OUT, name + 'OK.py')
if os.path.exists(prod):
    os.remove(prod)
p = subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', pyc, '-o', prod],
                   capture_output=True, encoding='utf-8', errors='replace')
print('--- product (rc=%s) ---' % p.returncode)
print(open(prod, encoding='utf-8').read())
if p.returncode != 0:
    print(p.stdout[-3000:])
    print(p.stderr[-3000:])

try:
    prod_code = compile(open(prod, encoding='utf-8').read(), name + 'OK.py', 'exec')
except SyntaxError as e:
    print('PRODUCT SYNTAX ERROR:', e)
    sys.exit(0)

orig = dict(all_codes(code))
new = dict(all_codes(prod_code))
print('--- bytecode compare ---')
for k in sorted(orig):
    a = dump(orig[k])
    b = dump(new.get(k)) if k in new else None
    if b is None:
        print('MISSING in product:', k)
        continue
    if a != b:
        print('DIFF', k)
        import difflib
        for l in difflib.unified_diff(a, b, 'orig', 'prod', lineterm='', n=1):
            print('   ', l)
    else:
        print('SAME', k)
for k in sorted(new):
    if k not in orig:
        print('EXTRA in product:', k)
