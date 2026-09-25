# -*- coding: utf-8 -*-
"""scratch: compile a .py in this directory into a bare 3.11 .pyc next to it."""
import importlib.util
import marshal
import os
import struct
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')


def make(src):
    code = compile(open(src, encoding='utf-8').read(), os.path.basename(src), 'exec')
    dst = src[:-3] + '.pyc'
    data = marshal.dumps(code, 4)
    header = importlib.util.MAGIC_NUMBER + struct.pack('<III', 0, int(time.time()) & 0xFFFFFFFF, len(data))
    open(dst, 'wb').write(header + data)
    print('wrote', dst, os.path.getsize(dst))


for s in sys.argv[1:]:
    make(s)
