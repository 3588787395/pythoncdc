# rr-v5r114 repro 1: _post 形——方法内 self.x = f(a, b or c) 值实参含 or 链
import sys, os, subprocess
REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r114diag'
PY = 'D:/Python/python.exe'

SRC = '''import re


class Version:
    def __init__(self, version, match):
        self._pre = _parse_letter_version(match.group("pre_l"), match.group("pre_n"))
        self._post = _parse_letter_version(
            match.group("post_l"), match.group("post_n1") or match.group("post_n2")
        )
        self._dev = _parse_letter_version(match.group("dev_l"), match.group("dev_n"))
        return
'''

src = OUT + '/repro1_postcall_src.py'
open(src, 'w', encoding='utf-8').write(SRC)
r = subprocess.run([PY, '-I', '-c', 'import py_compile; py_compile.compile(r"%s", r"%s", doraise=True)' % (src, OUT + '/repro1.pyc')], capture_output=True, text=True)
print('compile rc', r.returncode, r.stderr[:200])
r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/repro1.pyc', '-o', OUT + '/repro1_out.py'], capture_output=True, text=True, cwd=REPO)
print('decompile rc', r.returncode, r.stderr[:300])
print('=== product ===')
print(open(OUT + '/repro1_out.py', encoding='utf-8').read())
