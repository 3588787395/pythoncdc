# -*- coding: utf-8 -*-
"""scratch: print the exact LF-normalised source slice so a spec anchor can be cut."""
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
p = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'
u = io.open(p, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
lines = u.split('\n')
lo, hi = int(sys.argv[1]), int(sys.argv[2])
seg = '\n'.join(lines[lo - 1:hi])
print(seg)
print('=== occurrences of this exact slice in the LF text:', u.count(seg))
