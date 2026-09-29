# -*- coding: utf-8 -*-
"""fix1 arm runner: decompile one pyc with a mirror arm and write the product.

usage: python -X utf8 run_arm.py <arm> <pyc> <out.py>
"""
import io
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
GATE = r'D:/Temp/opencode/r75gate'

arm, pyc, out = sys.argv[1], sys.argv[2], sys.argv[3]
core = (REPO if arm == 'landed' else GATE + '/center/mirr_' + arm).replace('\\', '/')
sys.path.insert(0, core)
sys.path.append(REPO)
os.chdir(REPO)
import pycdc  # noqa: E402

got = os.path.dirname(os.path.abspath(pycdc.__file__)).replace('\\', '/')
assert got == core, 'pycdc resolved to %s not %s' % (got, core)
text = pycdc.decompile_pyc(pyc)
io.open(out, 'w', encoding='utf-8').write(text)
print('wrote %s (%d bytes) from arm=%s' % (out, len(text), arm))
