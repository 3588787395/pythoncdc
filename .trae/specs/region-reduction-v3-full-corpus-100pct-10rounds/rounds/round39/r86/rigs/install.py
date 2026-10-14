"""Install / restore the mirror's analyzer+generator bytes from named sources.

usage: python -X utf8 work/install.py <ana|gen|both> <src1> [<src2>]
  ana  -> core/cfg/region_analyzer.py
  gen  -> core/cfg/region_ast_generator.py
  both -> both, ana first then gen
Prints resulting sha16 for both files.
"""
import hashlib
import shutil
import sys

MIRROR = 'D:/Temp/r86'
TARGETS = {
    'ana': MIRROR + '/core/cfg/region_analyzer.py',
    'gen': MIRROR + '/core/cfg/region_ast_generator.py',
}
which = sys.argv[1]
srcs = sys.argv[2:]
order = ['ana', 'gen'] if which == 'both' else [which]
for w, s in zip(order, srcs):
    shutil.copyfile(s, TARGETS[w])
for w in ('ana', 'gen'):
    d = open(TARGETS[w], 'rb').read()
    print('%s sha16=%s bytes=%d' % (w, hashlib.sha256(d).hexdigest()[:16], len(d)))
