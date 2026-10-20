# -*- coding: utf-8 -*-
import io
import os
import sys
import traceback

sys.path.insert(0, os.getcwd())
buf = io.StringIO()
_old = sys.stdout
sys.stdout = buf
try:
    from pycdc import decompile_pyc
    src = decompile_pyc(r'test_repros\round7\r7_08_with_tryfin_constret.pyc')
except Exception:
    sys.stdout = _old
    traceback.print_exc()
else:
    sys.stdout = _old
    print('OK len', len(src))
    print(buf.getvalue()[-1500:])
