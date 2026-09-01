"""R26 测试工程师：反编译 quotation.pyc 并写入 /tmp/r26_decompiled.py"""
import sys
import time

sys.path.insert(0, '/workspace')

from pycdc import decompile_pyc

PYC = '/workspace/quotation.pyc'
OUT = '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_26/test_engineer/r26_decompiled.py'

t0 = time.time()
src = decompile_pyc(PYC, use_cfg=False, cfg_hybrid=False)
elapsed = time.time() - t0
print(f"[decompile] elapsed={elapsed:.2f}s, len={len(src)}")

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(src)

import shutil
shutil.copy(OUT, '/tmp/r26_decompiled.py')

print(f"[decompile] wrote {OUT}")
