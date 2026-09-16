import sys, os, traceback, types, marshal, io
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

from pycdc import decompile_pyc

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQData/utils/common_func.pyc'
source = decompile_pyc(pyc)
lines = source.split('\n')
in_f = False
fl = []
for l in lines:
    s = l.strip()
    if 'def handle_exrights' in s:
        in_f = True
        fl.append(l)
        continue
    if in_f:
        ci = len(l) - len(l.lstrip()) if l.strip() else 999
        di = len(fl[0]) - len(fl[0].lstrip()) if fl else 0
        if s and ci <= di and fl:
            break
        fl.append(l)

with open('d_temp/decompiled_source.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(fl[:5]))
