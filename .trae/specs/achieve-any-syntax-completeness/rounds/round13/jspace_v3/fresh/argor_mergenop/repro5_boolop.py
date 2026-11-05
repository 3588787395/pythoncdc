# rr-v5r114 repro 5: or 值链赋值 + 裸字符串语句（boolop 路径 NOP 丢失?）
import sys, os, subprocess
REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r114diag'
PY = 'D:/Python/python.exe'
SRC = '''import sys

if sys.version_info >= (3, 9):
    _flag = 1

_X = "a"
_Y = "b"
VAL = _X or _Y
"""
docstring between statements
"""
OTHER = "z"
'''
src = OUT + '/repro5_src.py'
open(src, 'w', encoding='utf-8').write(SRC)
subprocess.run([PY, '-I', '-c', 'import py_compile; py_compile.compile(r"%s", r"%s", doraise=True)' % (src, OUT + '/repro5.pyc')], capture_output=True)
r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/repro5.pyc', '-o', OUT + '/repro5_out.py'], capture_output=True, text=True, cwd=REPO)
print(open(OUT + '/repro5_out.py', encoding='utf-8').read())
