# -*- coding: utf-8 -*-
"""R8 probe: compile a source to .pyc and decompile it with pycdc, then verify."""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
os.chdir(ROOT)

src = sys.argv[1]
name = os.path.basename(src).replace('.py', '')
outdir = sys.argv[2] if len(sys.argv) > 2 else r'd:\Temp\opencode\r8'
os.makedirs(outdir, exist_ok=True)
pyc = os.path.join(outdir, name + '.pyc')
code = compile(open(src, encoding='utf-8').read(), name + '.py', 'exec')
import marshal
import importlib.util
with open(pyc, 'wb') as f:
    f.write(importlib.util.MAGIC_NUMBER)
    f.write(b'\x00' * 12)
    f.write(marshal.dumps(code))

prod = os.path.join(outdir, name + 'OK.py')
p = subprocess.run([sys.executable, '-X', 'utf8', 'pycdc.py', pyc, '-o', prod],
                   capture_output=True, encoding='utf-8', errors='replace')
print('regen rc', p.returncode)
print(p.stdout[-2000:])
print(p.stderr[-2000:])
print('--- product ---')
print(open(prod, encoding='utf-8').read())
