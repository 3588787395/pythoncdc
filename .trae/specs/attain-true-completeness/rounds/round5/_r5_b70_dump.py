# -*- coding: utf-8 -*-
"""R5 B70 evidence: ground-truth dis + current decompiled output for
rv9_02::while_with_whole_body."""
import dis
import io
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

out = open(os.path.join(HERE, '_r5_b70_dis.txt'), 'w', encoding='utf-8')

with open(r'test_repros\round9\rv9_02_b66_with_nest.pyc', 'rb') as f:
    code = marshal.loads(f.read()[16:])

for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'while_with_whole_body':
        out.write('=== ground truth dis: while_with_whole_body ===\n')
        dis.dis(c, file=out)
        break
out.close()

from pycdc import decompile_pyc  # noqa: E402

src = decompile_pyc(r'test_repros\round9\rv9_02_b66_with_nest.pyc')
open(os.path.join(HERE, '_r5_b70_gen.txt'), 'w', encoding='utf-8').write(src)
print('done')
