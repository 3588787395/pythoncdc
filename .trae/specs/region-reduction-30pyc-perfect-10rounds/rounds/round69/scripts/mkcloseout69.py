# -*- coding: utf-8 -*-
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\Temp\opencode\r69gate\center\closeout67.py'
DST = r'D:\Temp\opencode\r69gate\center\closeout69.py'
src = io.open(SRC, encoding='utf-8').read()
old = "    dirs += sorted(glob.glob(os.path.join(REPO, 'test_repros', 'round67_*')))"
add = (old + "\n"
       "    dirs += sorted(glob.glob(os.path.join(REPO, 'test_repros', 'round68_*')))\n"
       "    dirs += sorted(glob.glob(os.path.join(REPO, 'test_repros', 'round69_*')))")
assert src.count(old) == 1, src.count(old)
s = src.replace(old, add)
s = s.replace('Round 63 close-out helpers',
              'Round 69 close-out helpers (battery list now also covers round68/69 witnesses)')
assert 'round69_*' in s
io.open(DST, 'w', encoding='utf-8', newline='\n').write(s)
print('closeout69.py written')

import importlib.util as iu
sp = iu.spec_from_file_location('co69', DST)
m = iu.module_from_spec(sp)
sp.loader.exec_module(m)
print('battery list size now:', len(m.repro_list()))
