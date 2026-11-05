# rr-v5r115 repro 3: 内层 if 臂尾裸 return + 非互斥后随语句——运行时对照
import sys, os, subprocess
REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r115diag'
PY = 'D:/Python/python.exe'
SRC = '''class W:
    def m(self, state):
        self._log = []
        if isinstance(state, tuple):
            if len(state) == 6:
                self._p, self._q = state[:2]
                return ("six", self._p, self._q)
            if len(state) == 2:
                _, slot = state
                self._x = slot
        self._tail = 1
        return ("tail", getattr(self, "_x", None))
'''
src = OUT + '/repro3_src.py'
open(src, 'w', encoding='utf-8').write(SRC)
subprocess.run([PY, '-I', '-c', 'import py_compile; py_compile.compile(r"%s", r"%s", doraise=True)' % (src, OUT + '/repro3.pyc')], capture_output=True)
r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', OUT + '/repro3.pyc', '-o', OUT + '/repro3_out.py'], capture_output=True, text=True, cwd=REPO)
print('=== product ===')
print(open(OUT + '/repro3_out.py', encoding='utf-8').read())

import importlib.util
def load_mod_from_src(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
mo = load_mod_from_src(src, 'orig')
mp = load_mod_from_src(OUT + '/repro3_out.py', 'prod')
for label, mod in (('ORIG', mo), ('PROD', mp)):
    w = mod.W()
    r6 = w.m((1, 2, 3, 4, 5, 6))
    print('%s m(6-tuple) -> %r' % (label, r6))
    w2 = mod.W()
    r2 = w2.m((0, {'_x': 9}))
    print('%s m(2-tuple) -> %r' % (label, r2))
