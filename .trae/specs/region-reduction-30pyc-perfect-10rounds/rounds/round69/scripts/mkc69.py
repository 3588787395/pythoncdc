# -*- coding: utf-8 -*-
import io
import shutil

s = io.open(r'D:\Temp\opencode\r69gate\center\mbuild69.py', encoding='utf-8').read()
old = "ROOT = r'D:/Temp/opencode/r69gate'"
new = "ROOT = r'D:/Temp/opencode/r69gate/center'"
assert s.count(old) == 1, s.count(old)
s2 = s.replace(old, new)
io.open(r'D:\Temp\opencode\r69gate\center\mbuild69c.py', 'w', encoding='utf-8', newline='\n').write(s2)
import os
stray = r'D:\Temp\opencode\r69gate\mirr_m69'
if os.path.isdir(stray):
    shutil.rmtree(stray)
print('mbuild69c.py written, stray mirror removed')
