# -*- coding: utf-8 -*-
import io
import os

P = r'D:\Temp\opencode\r69gate\center\mkarchive69.py'
s = io.open(P, encoding='utf-8').read()
old = '''def copy(src, dst, name=None):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst if name is None else os.path.join(dst, name))'''
new = '''def copy(src, dst, name=None):
    # dst may be a directory (file keeps its basename) or a full file path
    if name is not None:
        dst2 = os.path.join(dst, name)
        os.makedirs(dst, exist_ok=True)
    elif os.path.isdir(dst) or dst.endswith(('/', os.sep)):
        os.makedirs(dst, exist_ok=True)
        dst2 = os.path.join(dst, os.path.basename(src))
    else:
        os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
        dst2 = dst
    shutil.copy2(src, dst2)'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(P, 'w', encoding='utf-8', newline='\n').write(s)

b = (r'F:\Downloads\pythoncdc-main\.trae\specs\region-reduction-30pyc-perfect-10rounds'
     r'\rounds\round69\batches\b1_diag1')
if os.path.isfile(b):
    os.remove(b)
    print('removed stray file', b)
print('patched copy()')
