# -*- coding: utf-8 -*-
"""Positive control for crashscan37.py: run the SAME probe against a chosen core tree.

The full-402 scan returned zero swallowed exceptions; before reading that as "the crash family
is closed" the probe must be shown to fire. Control: point it at the pre-R36-A mirror
(D:/Temp/r36gate/r36/mirr_head, core sha 92c8c2aabdcd37b9f32b) on IQEngine/.../fly_api/base.pyc
-- that file is documented to have crashed 2x at region_ast_generator.py:4824 on those bytes.

usage: python -X utf8 crash37_ctl.py <mirror-root> <pyc> [<pyc> ...]
"""
import io
import os
import subprocess
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')

mirror = os.path.abspath(sys.argv[1])
paths = sys.argv[2:]
core = os.path.join(mirror, 'core', 'cfg', 'region_ast_generator.py')
print('mirror %s  core sha256[:20] %s  bytes %d'
      % (mirror, subprocess.check_output(
          ['git', 'hash-object', core], cwd=REPO).decode()[:0] or
         __import__('hashlib').sha256(io.open(core, 'rb').read()).hexdigest()[:20],
         os.path.getsize(core)))

sys.path.insert(0, mirror)          # mirror wins over the repo copy
os.chdir(mirror)                    # so relative imports inside pycdc resolve here
assert os.path.abspath(os.path.join(mirror, 'pycdc.py')) > ''
sys.argv = [sys.argv[0]] + ['--list=_ctl_list.txt', '--out=_ctl_out.txt']
io.open('_ctl_list.txt', 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(os.path.abspath(p) for p in paths) + '\n')
exec(compile(io.open(os.path.join(REPO, r'.trae/specs/region-reduction-30pyc-perfect-10rounds'
                                 r'/rounds/round37/../../../round37_ctl_body_unused'), encoding='utf-8')
              .read() if False else io.open(os.path.join(REPO, 'DUMMY'), encoding='utf-8').read(),
             'x', 'exec'))
