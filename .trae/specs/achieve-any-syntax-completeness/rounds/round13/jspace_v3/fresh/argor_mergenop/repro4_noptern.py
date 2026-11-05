# rr-v5r114 repro 4: 三元赋值 + 前置 if 边界 + 裸字符串语句（贴近 REAL46-031 块结构）
import sys, os, subprocess
REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r114diag'
PY = 'D:/Python/python.exe'

SRC = '''import re
import sys

if sys.version_info >= (3, 9):
    _flag = "new"
else:
    _flag = "old"

_OLD = "old-pattern"
_NEW = "new-pattern"
VERSION_PATTERN = (
    _OLD
    if (sys.implementation.name == "cpython" and sys.version_info < (3, 11, 5))
    or (sys.implementation.name == "pypy" and sys.version_info < (3, 11, 13))
    or sys.version_info < (3, 11)
    else _NEW
)
"""
A string containing the regular expression used to match a valid version.
:meta hide-value:
"""
_LOCAL_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE | re.ASCII)
'''

src = OUT + '/repro4_noptern_src.py'
open(src, 'w', encoding='utf-8').write(SRC)
r = subprocess.run([PY, '-I', '-c', 'import py_compile; py_compile.compile(r"%s", r"%s", doraise=True)' % (src, OUT + '/repro4.pyc')], capture_output=True, text=True)
print('compile rc', r.returncode, r.stderr[:200])
r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/repro4.pyc', '-o', OUT + '/repro4_out.py'], capture_output=True, text=True, cwd=REPO)
print('decompile rc', r.returncode, r.stderr[:300])
print('=== product ===')
print(open(OUT + '/repro4_out.py', encoding='utf-8').read())
