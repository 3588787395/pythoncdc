import sys, io, os
sys.path.insert(0, '.')
from pycdc import decompile_pyc

r = decompile_pyc('site-packages/IQCommon/util/replace_utils.pyc')
lines = r.split('\n')
in_func = False
for i, l in enumerate(lines):
    if 'def decrypt_database_url' in l:
        in_func = True
    if in_func:
        print('%3d: %s' % (i, l))
    if in_func and l and not l.startswith(' ') and not l.startswith('def') and i > 0:
        if 'def ' not in l:
            in_func = False
