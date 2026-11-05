# rr-v5r114 repro 2: 模块级裸字符串表达式语句（属性 docstring 惯用法）→ 行标记 NOP
import sys, os, subprocess
REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r114diag'
PY = 'D:/Python/python.exe'

SRC = '''import re

VERSION_PATTERN = "abc"
"""
A string containing the regular expression used to match a valid version.
:meta hide-value:
"""
_LOCAL_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
'''

src = OUT + '/repro2_nop_src.py'
open(src, 'w', encoding='utf-8').write(SRC)
r = subprocess.run([PY, '-I', '-c', 'import py_compile; py_compile.compile(r"%s", r"%s", doraise=True)' % (src, OUT + '/repro2.pyc')], capture_output=True, text=True)
print('compile rc', r.returncode, r.stderr[:200])
r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/repro2.pyc', '-o', OUT + '/repro2_out.py'], capture_output=True, text=True, cwd=REPO)
print('decompile rc', r.returncode, r.stderr[:300])
print('=== product ===')
print(open(OUT + '/repro2_out.py', encoding='utf-8').read())
