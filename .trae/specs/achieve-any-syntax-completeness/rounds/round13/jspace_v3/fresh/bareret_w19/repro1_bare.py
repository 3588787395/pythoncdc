# rr-v5r115 repro 1: __setstate__ 形——if 臂尾裸 return + 后随第二 if
import sys, os, subprocess
REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r115diag'
PY = 'D:/Python/python.exe'
SRC = '''class V:
    def __setstate__(self, state):
        self._a = None
        self._b = None
        if isinstance(state, tuple):
            if len(state) == 6:
                self._p, self._q = state
                return
            if len(state) == 2:
                _, slot_dict = state
                if isinstance(slot_dict, dict):
                    self._x = slot_dict["_x"]
                    self._y = slot_dict["_y"]
                    return
        if isinstance(state, dict):
            version_nt = state.get("_v")
            if version_nt is not None:
                self._z = version_nt
'''
src = OUT + '/repro1_src.py'
open(src, 'w', encoding='utf-8').write(SRC)
subprocess.run([PY, '-I', '-c', 'import py_compile; py_compile.compile(r"%s", r"%s", doraise=True)' % (src, OUT + '/repro1.pyc')], capture_output=True)
r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/repro1.pyc', '-o', OUT + '/repro1_out.py'], capture_output=True, text=True, cwd=REPO)
print('rc', r.returncode)
print(open(OUT + '/repro1_out.py', encoding='utf-8').read())
