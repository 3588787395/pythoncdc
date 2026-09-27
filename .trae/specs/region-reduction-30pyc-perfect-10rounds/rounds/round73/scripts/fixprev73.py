# -*- coding: utf-8 -*-
import io
p = r'D:/Temp/opencode/r73gate/center/mkmirr_prev73.py'
t = io.open(p, encoding='utf-8').read()
old = "'core/cfg/comprehension_generator.py': ('be5490c1118c7199fe0a', 108192),"
new = "'core/cfg/comprehension_generator.py': ('b432a355809898525224', 115583),"
assert old in t, 'anchor missing'
t = t.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='').write(t)
print('patched; old present now:', old in t)
