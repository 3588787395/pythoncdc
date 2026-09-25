import py_compile
import os

d = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(d, 'r69d4_orchain.py')
out = os.path.join(d, 'r69d4_orchain.pyc')
py_compile.compile(src, cfile=out, doraise=True)
print('compiled', out, os.path.getsize(out))
